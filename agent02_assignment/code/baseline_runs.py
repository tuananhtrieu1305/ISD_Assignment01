"""Persist a registered baseline once; explicit resume from saved episode/RNG state."""

import json
import time
from dataclasses import asdict
from datetime import UTC, datetime

import numpy as np

from ..phase02 import disk_guard, save_csv, save_json
from ..workspace import inside, sha256_file
from .controlled import integer
from .reference_training import ReferenceSession
from .training import TrainSession, digest, q_digest


def new_session(track, market, learning, seed):
    if track not in ('REF', 'CONTROLLED'):
        raise ValueError('Unsupported baseline track')
    return (ReferenceSession if track == 'REF' else TrainSession)(market, learning, seed)


def summarize(rows, steps):
    rewards = np.array([[row['rl_episode_reward'], row['rule_episode_reward']] for row in rows])
    counts = np.array([row['action_counts'] for row in rows]).sum(axis=0)
    result = {'partition': 'training', 'episodes': len(rows), 'market_steps': len(rows)*steps,
              'rl_action_counts': counts[0].tolist(), 'rule_action_counts': counts[1].tolist()}
    for index, name in enumerate(('rl', 'rule')):
        values = rewards[:, index] / steps
        result.update({name+'_total_reward': float(rewards[:, index].sum()),
                       name+'_mean_reward_per_step': float(values.mean()),
                       name+'_first100_mean_per_step': float(values[:100].mean()),
                       name+'_last100_mean_per_step': float(values[-100:].mean()),
                       name+'_episode_mean_std_ddof1': float(values.std(ddof=1)) if len(values) > 1 else None})
    return result


def verify_run(base, run_id):
    prefix = 'artifacts/runs/' + run_id
    result = json.loads(inside(base, prefix + '/complete.json').read_text())
    for item in result['files']:
        path = inside(base, item['path'])
        if sha256_file(path) != item['sha256'] or path.stat().st_size != item['bytes']:
            raise ValueError('Run artifact hash/size mismatch: ' + item['path'])
    return result


def execute_run(base, spec, market, learning, declaration_sha256, *, resume=False, interval=100):
    integer(interval, 'checkpoint interval', 1)
    prefix = 'artifacts/runs/' + spec['run_id']
    folder = inside(base, prefix)
    registration = {'spec': spec, 'market': asdict(market), 'learning': asdict(learning),
                    'declaration_sha256': declaration_sha256}
    registration_hash = digest(registration)
    if (folder / 'complete.json').exists():
        result = verify_run(base, spec['run_id'])
        if result['registration_sha256'] != registration_hash:
            raise ValueError('Completed run registration changed')
        return result
    disk_guard(base)
    claim_path = folder / 'claim.json'
    if claim_path.exists():
        if not resume:
            raise FileExistsError('Incomplete claim requires explicit resume; do not replay')
        claim = json.loads(claim_path.read_text())
        if claim['registration_sha256'] != registration_hash:
            raise ValueError('Resume registration changed')
        checkpoints = sorted(folder.glob('checkpoint_e*.json'))
        saved = json.loads(checkpoints[-1].read_text())
        cls = ReferenceSession if spec['track'] == 'REF' else TrainSession
        run = cls.from_checkpoint(saved)
    else:
        run = new_session(spec['track'], market, learning, spec['seed'])
        save_json(base, prefix + '/claim.json', {'registration': registration,
                  'registration_sha256': registration_hash, 'started_utc': datetime.now(UTC).isoformat()})
        save_json(base, prefix + '/checkpoint_e000000.json', run.checkpoint())
    while run.completed < learning.episodes:
        start_episode = run.completed
        started, cpu_started = time.perf_counter(), time.process_time()
        status = 'COMPLETE'
        try:
            run.run_chunk(min(interval, learning.episodes-run.completed), trace_limit=20,
                          guard=lambda: disk_guard(base))
        except RuntimeError:
            status = 'PAUSED'
            raise
        finally:
            timing = {'start_episode': start_episode, 'end_episode': run.completed, 'status': status,
                      'train_wall_seconds': time.perf_counter()-started,
                      'train_cpu_seconds': time.process_time()-cpu_started}
            save_json(base, prefix + f'/checkpoint_e{run.completed:06d}.json', run.checkpoint())
            number = len(list(folder.glob('segment_*.json'))) + 1
            save_json(base, prefix + f'/segment_{number:04d}.json', timing)
    checkpoint = run.checkpoint()
    save_csv(base, prefix + '/episode_rewards.csv', run.rows)
    save_json(base, prefix + '/q_table.json', run.agent.q.tolist())
    save_json(base, prefix + '/visits.json', run.visits.tolist())
    save_json(base, prefix + '/trace_sample.json', run.trace)
    policy = [{'state': [d, other], 'q_no_discount': float(run.agent.q[d, other, 0]),
               'q_discount': float(run.agent.q[d, other, 1]), 'greedy_action_set': np.flatnonzero(
                   np.isclose(run.agent.q[d, other], run.agent.q[d, other].max())).tolist()}
              for d in (0, 1) for other in (0, 1)]
    save_json(base, prefix + '/policy.json', policy)
    summary = summarize(run.rows, market.steps)
    save_json(base, prefix + '/summary.json', summary)
    segments = [json.loads(path.read_text()) for path in sorted(folder.glob('segment_*.json'))]
    save_json(base, prefix + '/manifest.json', {**registration, 'registration_sha256': registration_hash,
              'device': 'NumPy CPU float64', 'checkpoint_payload_sha256': checkpoint['sha256'],
              'q_sha256': q_digest(run.agent.q), 'initialization': 'fresh zeros, not smoke checkpoint',
              'reference_execution': 'unchanged teacher classes, parity-tested instrumented loop'
              if spec['track'] == 'REF' else 'frozen Phase2 TrainSession'})
    paths = sorted(path for path in folder.rglob('*') if path.is_file())
    result = {'status': 'COMPLETE', 'run_id': spec['run_id'], 'registration_sha256': registration_hash,
              'summary': summary, 'q_sha256': q_digest(run.agent.q), 'resumed': resume,
              'train_wall_seconds': sum(row['train_wall_seconds'] for row in segments),
              'train_cpu_seconds': sum(row['train_cpu_seconds'] for row in segments),
              'files': [{'path': path.relative_to(base).as_posix(), 'sha256': sha256_file(path),
                         'bytes': path.stat().st_size} for path in paths]}
    save_json(base, prefix + '/complete.json', result)
    return verify_run(base, spec['run_id'])
