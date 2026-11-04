"""Episode-boundary checkpoints record Q, logs and every independent RNG stream."""

import copy
import hashlib
import json
from dataclasses import asdict

import numpy as np

from .controlled import LearningConfig, MarketConfig, MarketEnv, QAgent, RuleAgent, integer


def digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def q_digest(q):
    array = np.asarray(q, dtype='<f8')
    if array.shape != (2, 2, 2) or not np.isfinite(array).all():
        raise ValueError('Expected finite 2x2x2 Q table')
    return hashlib.sha256(array.tobytes(order='C')).hexdigest()


class TrainSession:
    def __init__(self, market, learning, seed):
        self.market, self.learning, self.seed = market, learning, integer(seed, 'seed')
        self.env = MarketEnv(market, seed)
        # Distinct from demand and sales; shared across configs for paired seeds.
        self.agent = QAgent(learning, int(np.random.SeedSequence([seed, 3]).generate_state(1)[0]))
        self.rule = RuleAgent()
        self.completed, self.rows, self.trace = 0, [], []
        self.visits = np.zeros((2, 2, 2), dtype=np.int64)

    def run_chunk(self, episodes, *, trace_limit=0, guard=None):
        integer(episodes, 'chunk episodes', 1)
        integer(trace_limit, 'trace_limit')
        if self.completed + episodes > self.learning.episodes:
            raise ValueError('Chunk exceeds declared episode budget')
        for _ in range(episodes):
            if guard is not None:
                guard()
            states = self.env.reset()
            total, counts = np.zeros(2), np.zeros((2, 2), dtype=np.int64)
            epsilon = self.learning.epsilon_at(self.completed)
            for step in range(self.market.steps):
                # Neither policy sees the other's current action before choosing.
                actions = (self.agent.act(states[0], epsilon), self.rule.act(states[1]))
                result = self.env.step(actions)
                self.agent.learn(states[0], actions[0], result.rewards[0], result.states[0], result.done)
                self.visits[(*states[0], actions[0])] += 1
                total += result.rewards
                for role in range(2):
                    counts[role, actions[role]] += 1
                if len(self.trace) < trace_limit:
                    self.trace.append({'episode': self.completed+1, 'step': step+1,
                                       'states_before': [list(s) for s in states], 'actions': list(actions),
                                       'rewards': list(result.rewards), 'states_after': [list(s) for s in result.states],
                                       'sales': list(result.sales), 'terminal': result.done})
                states = result.states
            self.completed += 1
            self.rows.append({'episode': self.completed, 'rl_episode_reward': float(total[0]),
                              'rule_episode_reward': float(total[1]),
                              'rl_mean_reward_per_step': float(total[0] / self.market.steps),
                              'rule_mean_reward_per_step': float(total[1] / self.market.steps),
                              'epsilon': epsilon, 'alpha': self.learning.alpha, 'action_counts': counts.tolist()})

    def checkpoint(self):
        state = {'schema': 'ag02.controlled.checkpoint.1', 'market': asdict(self.market),
                 'learning': asdict(self.learning), 'seed': self.seed, 'completed': self.completed,
                 'q': self.agent.q.tolist(), 'visits': self.visits.tolist(), 'rows': self.rows, 'trace': self.trace,
                 'rng': {'demand': self.env.demand_rng.bit_generator.state,
                         'sales': [rng.bit_generator.state for rng in self.env.sales_rngs],
                         'agent': self.agent.rng.bit_generator.state}}
        return copy.deepcopy({**state, 'sha256': digest(state)})

    @classmethod
    def from_checkpoint(cls, saved):
        state = copy.deepcopy(saved)
        fingerprint = state.pop('sha256')
        if state['schema'] != 'ag02.controlled.checkpoint.1' or digest(state) != fingerprint:
            raise ValueError('Checkpoint schema/hash mismatch')
        result = cls(MarketConfig(**state['market']), LearningConfig(**state['learning']), state['seed'])
        result.completed = integer(state['completed'], 'completed')
        if result.completed > result.learning.episodes or len(state['rows']) != result.completed:
            raise ValueError('Checkpoint count mismatch')
        q_digest(state['q'])
        result.agent.q[:] = state['q']
        visits = np.asarray(state['visits'])
        if visits.shape != (2, 2, 2) or (visits < 0).any() or visits.sum() != result.completed * result.market.steps:
            raise ValueError('Checkpoint visits mismatch')
        result.visits[:] = visits
        result.rows, result.trace = state['rows'], state['trace']
        result.env.demand_rng.bit_generator.state = state['rng']['demand']
        for rng, value in zip(result.env.sales_rngs, state['rng']['sales'], strict=True):
            rng.bit_generator.state = value
        result.agent.rng.bit_generator.state = state['rng']['agent']
        return result
