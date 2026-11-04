"""Bounded Phase 2 smoke only; no full-training or final-evaluation entry point."""

import argparse
import csv
import io
import json
import shutil
import time
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from .code.controlled import LearningConfig, MarketConfig
from .code.evaluation.frozen import evaluate_dev
from .code.reference_adapter import reference_smoke
from .code.training import TrainSession, digest, q_digest
from .phase01 import preflight
from .protocol import build_protocol
from .workspace import inside, sha256_file, write_receipt

BASE = Path(__file__).resolve().parent
SMOKE = 'evidence/phase02/smoke'
SOURCE_FILES = ('code/__init__.py', 'code/controlled.py', 'code/training.py',
                'code/evaluation/__init__.py', 'code/evaluation/frozen.py',
                'code/reference_adapter.py', 'protocol.py', 'phase02.py', 'workspace.py')


def disk_guard(base):
    free = shutil.disk_usage(base)[2]
    if free < 5 * 1024**3:
        raise RuntimeError('Disk reserve requires at least 5 GiB; do not delete or alter system settings')
    return free


def save_json(base, relative, value):
    # Validate finite values before creating a file; workspace helper enforces paths/no overwrite.
    normalized = json.loads(json.dumps(value, allow_nan=False))
    return write_receipt(base, relative, normalized)


def save_csv(base, relative, rows):
    target = inside(base, relative)
    stream = io.StringIO(newline='')
    fields = list(rows[0])
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows({key: json.dumps(value) if isinstance(value, (list, dict)) else value
                     for key, value in row.items()} for row in rows)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8', newline='') as output:
        output.write(stream.getvalue())
    return target


def verify_smoke(base):
    receipt = json.loads(inside(base, SMOKE + '/complete.json').read_text())
    for item in receipt['files']:
        target = inside(base, item['path'])
        if sha256_file(target) != item['sha256'] or target.stat().st_size != item['bytes']:
            raise ValueError('Smoke artifact hash/size mismatch: ' + item['path'])
    for item in receipt['source_files']:
        if sha256_file(BASE / item['path']) != item['sha256']:
            raise ValueError('Smoke source hash mismatch: ' + item['path'])
    return receipt


def execute_smoke(base, protocol):
    fingerprint = digest(protocol)
    if inside(base, SMOKE + '/complete.json').exists():
        receipt = verify_smoke(base)
        if receipt['protocol_sha256'] != fingerprint:
            raise ValueError('Completed smoke belongs to a different protocol')
        return receipt
    claim = inside(base, SMOKE + '/claim.json')
    if claim.exists():
        raise FileExistsError('Existing smoke claim without completion; preserve and investigate, never replay')
    free_before = disk_guard(base)
    # Exclusive creation prevents two writers from running the same smoke.
    save_json(base, SMOKE + '/claim.json', {'status': 'claimed', 'protocol_sha256': fingerprint,
              'started_utc': datetime.now(UTC).isoformat(), 'purpose': 'SMOKE_NOT_REPORT'})
    smoke = protocol['smoke']
    episodes = smoke['episodes_per_track']
    reference = reference_smoke(episodes=episodes, seed=smoke['reference_seed'])
    disk_guard(base)
    save_json(base, SMOKE + '/reference/receipt.json', reference)
    save_csv(base, SMOKE + '/reference/episode_rewards.csv', reference['rows'])
    save_json(base, SMOKE + '/reference/q_table.json', reference['q'])
    sources = [{'path': p, 'sha256': sha256_file(BASE / p)} for p in SOURCE_FILES]
    save_json(base, SMOKE + '/reference/manifest.json', {
        'run_id': f'phase02_smoke/REF/s{smoke["reference_seed"]}', 'purpose': 'SMOKE_NOT_REPORT',
        'seed': smoke['reference_seed'], 'episodes': episodes,
        'reference_sha256': reference['reference_sha256'], 'protocol_sha256': fingerprint})
    learning = replace(LearningConfig(), episodes=episodes)
    run = TrainSession(MarketConfig(), learning, smoke['controlled_seed'])
    started = time.perf_counter()
    try:
        run.run_chunk(episodes, trace_limit=20, guard=lambda: disk_guard(base))
    except RuntimeError:
        save_json(base, SMOKE + f'/controlled/paused_e{run.completed:06d}.json', run.checkpoint())
        raise
    controlled_seconds = time.perf_counter() - started
    saved = run.checkpoint()
    checkpoint_path = SMOKE + f'/controlled/checkpoint_e{run.completed:06d}.json'
    save_json(base, checkpoint_path, saved)
    restored = TrainSession.from_checkpoint(json.loads(inside(base, checkpoint_path).read_text()))
    if restored.checkpoint() != saved:
        raise ValueError('Serialized checkpoint did not roundtrip exactly')
    save_csv(base, SMOKE + '/controlled/episode_rewards.csv', run.rows)
    save_json(base, SMOKE + '/controlled/q_table.json', run.agent.q.tolist())
    policy = [{'state': [d, other], 'greedy_action_set': np.flatnonzero(np.isclose(
               run.agent.q[d, other], run.agent.q[d, other].max())).tolist()}
              for d in (0, 1) for other in (0, 1)]
    save_json(base, SMOKE + '/controlled/policy.json', policy)
    save_json(base, SMOKE + '/controlled/visits.json', run.visits.tolist())
    save_json(base, SMOKE + '/controlled/trace_sample.json', run.trace)
    save_json(base, SMOKE + '/controlled/manifest.json', {
        'run_id': f'phase02_smoke/CONTROLLED/s{run.seed}', 'purpose': 'SMOKE_NOT_REPORT',
        'config': {'market': saved['market'], 'learning': saved['learning'], 'seed': run.seed},
        'config_sha256': digest({'market': saved['market'], 'learning': saved['learning'], 'seed': run.seed}),
        'protocol_sha256': fingerprint, 'source_files': sources,
        'checkpoint_path': checkpoint_path, 'checkpoint_payload_sha256': saved['sha256']})
    before = run.checkpoint()
    dev = [evaluate_dev(run.agent.q, run.market, episodes=smoke['development_episodes_per_role'],
                       scenario_seed=smoke['development_scenario_seed'], role=role) for role in (0, 1)]
    if before != run.checkpoint():
        raise ValueError('DEV evaluation changed training state or RNG')
    save_json(base, SMOKE + '/development.json', {'purpose': 'frozen_DEV_smoke_only', 'roles': dev})
    paths = sorted(path for path in inside(base, SMOKE).rglob('*') if path.is_file())
    records = [{'path': path.relative_to(base).as_posix(), 'bytes': path.stat().st_size,
                'sha256': sha256_file(path)} for path in paths]
    receipt = {'status': 'PASS', 'purpose': 'SMOKE_NOT_REPORT', 'protocol_sha256': fingerprint,
               'episodes_per_track': episodes, 'training_market_steps': episodes * run.market.steps * 2,
               'development_market_steps': sum(item['steps'] for item in dev), 'full_training_started': False,
               'final_evaluation_started': False, 'reference_main_called': False, 'charts_generated': 0,
               'checkpoint_roundtrip_exact': True, 'evaluation_training_state_unchanged': True,
               'controlled_q_sha256': q_digest(run.agent.q), 'files': records,
               'source_files': sources,
               'host_free_bytes_before': free_before, 'host_free_bytes_after': disk_guard(base),
               'wall_seconds': {'reference': reference['wall_seconds'], 'controlled': controlled_seconds},
               'artifact_bytes_excluding_complete': sum(item['bytes'] for item in records),
               'completed_utc': datetime.now(UTC).isoformat()}
    save_json(base, SMOKE + '/complete.json', receipt)
    return verify_smoke(base)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', choices=('status', 'write-protocol', 'smoke', 'verify-smoke'))
    args = parser.parse_args()
    current = preflight()
    protocol = build_protocol()
    if args.task == 'write-protocol':
        save_json(BASE, 'docs/protocol_v1.json', protocol)
        result = {'status': 'PASS', 'path': 'docs/protocol_v1.json', 'sha256': digest(protocol)}
    elif args.task == 'smoke':
        saved_protocol = json.loads((BASE / 'docs/protocol_v1.json').read_text())
        if digest(saved_protocol) != digest(protocol):
            raise ValueError('Protocol differs; preserve existing registration and create a revision')
        result = execute_smoke(BASE, saved_protocol)
    elif args.task == 'verify-smoke':
        result = verify_smoke(BASE)
    else:
        result = {'status': current['status'], 'phase': 2, 'declared_runs': len(protocol['training_runs']),
                  'full_training_started': False, 'final_evaluation_started': False,
                  'smoke_complete': (BASE / SMOKE / 'complete.json').exists()}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
