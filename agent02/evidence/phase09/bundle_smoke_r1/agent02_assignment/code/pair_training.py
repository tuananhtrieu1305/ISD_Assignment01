"""Two simultaneously learning tabular agents, independent policy RNGs and exact resume."""

import copy
import json
import time
from dataclasses import asdict

import numpy as np

from ..phase02 import disk_guard, save_csv, save_json
from ..workspace import inside, sha256_file
from .baseline_runs import verify_run
from .controlled import LearningConfig, MarketConfig, MarketEnv, QAgent, integer
from .training import digest, q_digest


class PairSession:
    def __init__(self, market, learning, seed):
        self.market, self.learning, self.seed = market, learning, integer(seed, 'seed')
        self.env = MarketEnv(market, seed)
        self.agents = [QAgent(learning, int(np.random.SeedSequence([seed, channel]).generate_state(1)[0]))
                       for channel in (3, 4)]
        self.completed, self.rows, self.trace = 0, [], []
        self.visits = np.zeros((2, 2, 2, 2), dtype=np.int64)

    def run_chunk(self, episodes, *, trace_limit=0, guard=None):
        integer(episodes, 'chunk episodes', 1)
        integer(trace_limit, 'trace_limit')
        if self.completed+episodes > self.learning.episodes:
            raise ValueError('Chunk exceeds episode budget')
        for _ in range(episodes):
            if guard is not None:
                guard()
            states = self.env.reset()
            total, counts = np.zeros(2), np.zeros((2, 2), dtype=np.int64)
            epsilon = self.learning.epsilon_at(self.completed)
            for step in range(self.market.steps):
                actions = tuple(agent.act(states[i], epsilon) for i, agent in enumerate(self.agents))
                result = self.env.step(actions)
                for i, agent in enumerate(self.agents):
                    agent.learn(states[i], actions[i], result.rewards[i], result.states[i], result.done)
                    self.visits[(i, *states[i], actions[i])] += 1
                    counts[i, actions[i]] += 1
                total += result.rewards
                if len(self.trace) < trace_limit:
                    self.trace.append({'episode': self.completed+1, 'step': step+1,
                        'states_before': [list(s) for s in states], 'actions': list(actions),
                        'rewards': list(result.rewards), 'states_after': [list(s) for s in result.states],
                        'sales': list(result.sales), 'terminal': result.done})
                states = result.states
            self.completed += 1
            self.rows.append({'episode': self.completed, 'agent0_episode_reward': float(total[0]),
                'agent1_episode_reward': float(total[1]), 'agent0_mean_reward_per_step': float(total[0]/self.market.steps),
                'agent1_mean_reward_per_step': float(total[1]/self.market.steps),
                'epsilon': epsilon, 'alpha': self.learning.alpha, 'action_counts': counts.tolist()})

    def checkpoint(self):
        value = {'schema': 'ag02.pair.checkpoint.1', 'market': asdict(self.market), 'learning': asdict(self.learning),
            'seed': self.seed, 'completed': self.completed, 'q': [a.q.tolist() for a in self.agents],
            'visits': self.visits.tolist(), 'rows': self.rows, 'trace': self.trace,
            'rng': {'demand': self.env.demand_rng.bit_generator.state,
                'sales': [r.bit_generator.state for r in self.env.sales_rngs],
                'agents': [a.rng.bit_generator.state for a in self.agents]}}
        return copy.deepcopy({**value, 'sha256': digest(value)})

    @classmethod
    def from_checkpoint(cls, saved):
        value = copy.deepcopy(saved)
        fingerprint = value.pop('sha256')
        if value['schema'] != 'ag02.pair.checkpoint.1' or digest(value) != fingerprint:
            raise ValueError('Pair checkpoint schema/hash mismatch')
        result = cls(MarketConfig(**value['market']), LearningConfig(**value['learning']), value['seed'])
        result.completed = integer(value['completed'], 'completed')
        if result.completed > result.learning.episodes or len(value['rows']) != result.completed:
            raise ValueError('Checkpoint episode mismatch')
        for agent, q, rng in zip(result.agents, value['q'], value['rng']['agents'], strict=True):
            q_digest(q)
            agent.q[:] = q
            agent.rng.bit_generator.state = rng
        visits = np.asarray(value['visits'])
        if (visits.shape != (2, 2, 2, 2) or (visits < 0).any() or
                not np.all(visits.sum(axis=(1, 2, 3)) == result.completed*result.market.steps)):
            raise ValueError('Checkpoint visits mismatch')
        result.visits[:] = visits
        result.rows, result.trace = value['rows'], value['trace']
        result.env.demand_rng.bit_generator.state = value['rng']['demand']
        for rng, state in zip(result.env.sales_rngs, value['rng']['sales'], strict=True):
            rng.bit_generator.state = state
        return result


def execute_pair(base, spec, market, learning, proof, *, interval=100, resume=False):
    integer(interval, 'interval', 1)
    prefix = 'artifacts/runs/'+spec['run_id']
    folder = inside(base, prefix)
    registration = {'spec': spec, 'market': asdict(market), 'learning': asdict(learning), 'declaration_sha256': proof}
    fingerprint = digest(registration)
    if (folder/'complete.json').exists():
        result = verify_run(base, spec['run_id'])
        if result['registration_sha256'] != fingerprint:
            raise ValueError('Completed pair registration changed')
        return result
    disk_guard(base)
    if (folder/'claim.json').exists():
        if not resume:
            raise FileExistsError('Incomplete pair requires explicit resume')
        if json.loads((folder/'claim.json').read_text())['registration_sha256'] != fingerprint:
            raise ValueError('Resume registration changed')
        run = PairSession.from_checkpoint(json.loads(max(folder.glob('checkpoint_e*.json')).read_text()))
    else:
        run = PairSession(market, learning, spec['seed'])
        save_json(base, prefix+'/claim.json', {'registration': registration, 'registration_sha256': fingerprint})
        save_json(base, prefix+'/checkpoint_e000000.json', run.checkpoint())
    while run.completed < learning.episodes:
        start, wall, cpu = run.completed, time.perf_counter(), time.process_time()
        status = 'COMPLETE'
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
    save_json(base, prefix+'/q_table.json', [a.q.tolist() for a in run.agents])
    save_json(base, prefix+'/visits.json', run.visits.tolist())
    save_json(base, prefix+'/trace_sample.json', run.trace)
    policy = [{'learner': i, 'state': [d, other], 'q_values': a.q[d, other].tolist(),
        'greedy_actions': np.flatnonzero(np.isclose(a.q[d, other], a.q[d, other].max())).tolist()}
        for i, a in enumerate(run.agents) for d in (0, 1) for other in (0, 1)]
    save_json(base, prefix+'/policy.json', policy)
    summary = {'episodes': run.completed, 'market_steps': run.completed*market.steps,
               'learners': 2, 'train_mean_per_step': [float(np.mean([r[f'agent{i}_mean_reward_per_step'] for r in run.rows]))
                                                   for i in (0, 1)]}
    save_json(base, prefix+'/summary.json', summary)
    save_json(base, prefix+'/manifest.json', {**registration, 'device': 'NumPy CPU float64',
        'initialization': 'fresh zero Q for both learners', 'policy_rng_channels': [3, 4]})
    segments = [json.loads(p.read_text()) for p in sorted(folder.glob('segment_*.json'))]
    paths = sorted(p for p in folder.rglob('*') if p.is_file())
    result = {'status': 'COMPLETE', 'run_id': spec['run_id'], 'registration_sha256': fingerprint,
        'summary': summary, 'q_sha256': [q_digest(a.q) for a in run.agents], 'resumed': resume,
        'train_wall_seconds': sum(s['train_wall_seconds'] for s in segments),
        'train_cpu_seconds': sum(s['train_cpu_seconds'] for s in segments),
        'files': [{'path': p.relative_to(base).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha256_file(p)} for p in paths]}
    save_json(base, prefix+'/complete.json', result)
    return verify_run(base, spec['run_id'])
