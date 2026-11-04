"""Persist preregistered augmented runs with explicit episode/RNG resume and immutable DONE."""

import json
import time
from dataclasses import asdict
from itertools import product

import numpy as np

from ..phase02 import disk_guard, save_csv, save_json
from ..workspace import inside, sha256_file
from .augmented import AugmentedSession, augmented_hash, state_index
from .baseline_runs import summarize, verify_run
from .controlled import integer
from .training import digest


def execute_augmented(base, spec, market, learning, proof, *, interval=100, resume=False):
    integer(interval, 'interval', 1)
    prefix = 'artifacts/runs/'+spec['run_id']
    folder = inside(base, prefix)
    registration = {'spec': spec, 'market': asdict(market), 'learning': asdict(learning), 'declaration_sha256': proof}
    fingerprint = digest(registration)
    if (folder/'complete.json').exists():
        saved = verify_run(base, spec['run_id'])
        if saved['registration_sha256']!=fingerprint:
            raise ValueError('Completed augmented registration changed')
        return saved
    disk_guard(base)
    if (folder/'claim.json').exists():
        if not resume:
            raise FileExistsError('Incomplete augmented claim requires explicit resume')
        if json.loads((folder/'claim.json').read_text())['registration_sha256']!=fingerprint:
            raise ValueError('Resume registration changed')
        run = AugmentedSession.from_checkpoint(json.loads(max(folder.glob('checkpoint_e*.json')).read_text()))
    else:
        run = AugmentedSession(market, learning, spec['seed'])
        save_json(base, prefix+'/claim.json', {'registration': registration, 'registration_sha256': fingerprint})
        save_json(base, prefix+'/checkpoint_e000000.json', run.checkpoint())
    while run.completed<learning.episodes:
        start, wall, cpu, status = run.completed, time.perf_counter(), time.process_time(), 'COMPLETE'
        try:
            run.run_chunk(min(interval, learning.episodes-run.completed), trace_limit=20, guard=lambda: disk_guard(base))
        except BaseException:
            status = 'PAUSED'
            raise
        finally:
            timing = {'start_episode': start, 'end_episode': run.completed, 'status': status,
                'train_wall_seconds': time.perf_counter()-wall, 'train_cpu_seconds': time.process_time()-cpu}
            save_json(base, prefix+f'/checkpoint_e{run.completed:06d}.json', run.checkpoint())
            number = len(list(folder.glob('segment_*.json')))+1
            save_json(base, prefix+f'/segment_{number:04d}.json', timing)
    save_csv(base, prefix+'/episode_rewards.csv', run.rows)
    save_json(base, prefix+'/q_table.json', run.agent.q.tolist())
    save_json(base, prefix+'/visits.json', run.visits.tolist())
    save_json(base, prefix+'/trace_sample.json', run.trace)
    policies = []
    for d, own, other, remaining in product((0,1), (0,1), (0,1), range(1,21)):
        state = (d,own,other,remaining)
        values = run.agent.q[state_index(state)]
        policies.append({'state': list(state), 'q_values': values.tolist(),
            'greedy_actions': np.flatnonzero(np.isclose(values, values.max())).tolist(),
            'visits': run.visits[state_index(state)].tolist()})
    save_json(base, prefix+'/policy.json', policies)
    summary = {**summarize(run.rows, market.steps), 'q_entries': 320,
        'visited_state_action_cells': int(np.count_nonzero(run.visits)), 'q_payload_bytes_float64': int(run.agent.q.nbytes)}
    save_json(base, prefix+'/summary.json', summary)
    save_json(base, prefix+'/manifest.json', {**registration, 'device': 'NumPy CPU float64',
        'state_order': ['demand','own_previous','competitor_previous','remaining_steps'],
        'q_axis_order': ['demand','own_previous','competitor_previous','remaining_minus1','action'],
        'q_sha256': augmented_hash(run.agent.q), 'initialization': 'fresh zero Q, no oracle labels'})
    segments = [json.loads(p.read_text()) for p in sorted(folder.glob('segment_*.json'))]
    paths = sorted(p for p in folder.rglob('*') if p.is_file())
    result = {'status': 'COMPLETE', 'run_id': spec['run_id'], 'registration_sha256': fingerprint, 'summary': summary,
        'q_sha256': augmented_hash(run.agent.q), 'resumed': resume,
        'train_wall_seconds': sum(s['train_wall_seconds'] for s in segments),
        'train_cpu_seconds': sum(s['train_cpu_seconds'] for s in segments),
        'files': [{'path':p.relative_to(base).as_posix(), 'bytes':p.stat().st_size, 'sha256':sha256_file(p)} for p in paths]}
    save_json(base, prefix+'/complete.json', result)
    return verify_run(base, spec['run_id'])
