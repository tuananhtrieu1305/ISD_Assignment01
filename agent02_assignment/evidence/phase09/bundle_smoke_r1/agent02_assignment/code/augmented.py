"""Tabular Q with own history and remaining time; market/reward stay unchanged."""

import copy
import hashlib
from dataclasses import asdict

import numpy as np

from .controlled import (
    LearningConfig,
    MarketConfig,
    MarketEnv,
    RuleAgent,
    binary,
    conversion,
    integer,
    margin,
)
from .training import digest

SHAPE = (2, 2, 2, 20, 2)


def state_index(state):
    if not isinstance(state, (tuple, list)) or len(state)!=4:
        raise ValueError('State must be demand,own_previous,other_previous,remaining')
    remaining = integer(state[3], 'remaining', 1)
    if remaining>20:
        raise ValueError('Remaining exceeds registered horizon20')
    return (*[binary(v) for v in state[:3]], remaining-1)


def observe(env, role):
    binary(role, 'role')
    if not env.ready or env.elapsed>=env.config.steps:
        raise RuntimeError('Observation only exists for a live episode')
    return (env.demand, env.previous[role], env.previous[1-role], env.config.steps-env.elapsed)


def augmented_hash(q):
    array = np.asarray(q, dtype='<f8')
    if array.shape!=SHAPE or not np.isfinite(array).all():
        raise ValueError('Expected finite2x2x2x20x2 augmented Q')
    return hashlib.sha256(array.tobytes(order='C')).hexdigest()


def alias_witness():
    market, rule = MarketConfig(), RuleAgent()
    observations = [(1, own, 0, 20) for own in (0, 1)]
    other = [rule.act((1, own)) for own in (0, 1)]
    return {'old_observation_a': [1, 0], 'old_observation_b': [1, 0],
        'new_observation_a': list(observations[0]), 'new_observation_b': list(observations[1]),
        'rule_current_actions': other,
        'expected_reward_keep_price': [market.customers_high*conversion(1, 0, a)*margin(market, 0) for a in other],
        'interpretation': 'Same old local observation hides own previous action that changes fixed rule current action; analytic fixture, not a final trajectory'}


class AugmentedAgent:
    def __init__(self, learning, seed):
        self.config = learning
        self.rng = np.random.default_rng(integer(seed, 'seed'))
        self.q = np.zeros(SHAPE, dtype=np.float64)

    def act(self, state, epsilon, *, explore=True):
        values = self.q[state_index(state)]
        if not np.isfinite(epsilon) or not 0<=epsilon<=1 or not np.isfinite(values).all():
            raise ValueError('Invalid epsilon or Q')
        if explore and self.rng.random()<epsilon:
            return int(self.rng.integers(2))
        best = np.flatnonzero(np.isclose(values, values.max(), rtol=1e-5, atol=1e-8))
        return int(self.rng.choice(best))

    def learn(self, state, action, reward, following, terminal):
        index = state_index(state)
        action = binary(action, 'action')
        if not np.isfinite(reward) or bool(terminal)!=(state[3]==1):
            raise ValueError('Invalid reward/terminal time')
        if terminal:
            target = reward
        else:
            following_index = state_index(following)
            if following[3]!=state[3]-1:
                raise ValueError('Remaining time must decrease exactly1')
            target = reward+self.config.gamma*float(self.q[following_index].max())
        key = (*index, action)
        self.q[key] += self.config.alpha*(target-self.q[key])
        if not np.isfinite(self.q[key]):
            raise ValueError('Nonfinite augmented Q update')


class AugmentedSession:
    def __init__(self, market, learning, seed):
        if market.steps>20:
            raise ValueError('Augmented table supports horizon<=20')
        self.market, self.learning, self.seed = market, learning, integer(seed, 'seed')
        self.env, self.rule = MarketEnv(market, seed), RuleAgent()
        self.agent = AugmentedAgent(learning, int(np.random.SeedSequence([seed, 3]).generate_state(1)[0]))
        self.completed, self.rows, self.trace = 0, [], []
        self.visits = np.zeros(SHAPE, dtype=np.int64)

    def run_chunk(self, episodes, *, trace_limit=0, guard=None):
        integer(episodes, 'episodes', 1)
        integer(trace_limit, 'trace_limit')
        if self.completed+episodes>self.learning.episodes:
            raise ValueError('Chunk exceeds registered episode budget')
        for _ in range(episodes):
            if guard is not None:
                guard()
            states = self.env.reset()
            total, counts = np.zeros(2), np.zeros((2, 2), dtype=np.int64)
            epsilon = self.learning.epsilon_at(self.completed)
            for step in range(self.market.steps):
                observation = observe(self.env, 0)
                actions = (self.agent.act(observation, epsilon), self.rule.act(states[1]))
                result = self.env.step(actions)
                following = None if result.done else observe(self.env, 0)
                self.agent.learn(observation, actions[0], result.rewards[0], following, result.done)
                self.visits[(*state_index(observation), actions[0])] += 1
                total += result.rewards
                for role in (0, 1):
                    counts[role, actions[role]] += 1
                if len(self.trace)<trace_limit:
                    self.trace.append({'episode': self.completed+1, 'step': step+1,
                        'states_before': [list(s) for s in states], 'augmented_state_before': list(observation),
                        'actions': list(actions), 'rewards': list(result.rewards),
                        'augmented_state_after': list(following) if following is not None else None,
                        'states_after': [list(s) for s in result.states], 'sales': list(result.sales), 'terminal': result.done})
                states = result.states
            self.completed += 1
            self.rows.append({'episode': self.completed, 'rl_episode_reward': float(total[0]),
                'rule_episode_reward': float(total[1]), 'rl_mean_reward_per_step': float(total[0]/self.market.steps),
                'rule_mean_reward_per_step': float(total[1]/self.market.steps), 'epsilon': epsilon,
                'alpha': self.learning.alpha, 'action_counts': counts.tolist()})

    def checkpoint(self):
        value = {'schema': 'ag02.augmented.checkpoint.1', 'market': asdict(self.market), 'learning': asdict(self.learning),
            'seed': self.seed, 'completed': self.completed, 'q': self.agent.q.tolist(), 'visits': self.visits.tolist(),
            'rows': self.rows, 'trace': self.trace,
            'rng': {'demand': self.env.demand_rng.bit_generator.state,
                'sales': [r.bit_generator.state for r in self.env.sales_rngs], 'agent': self.agent.rng.bit_generator.state}}
        return copy.deepcopy({**value, 'sha256': digest(value)})

    @classmethod
    def from_checkpoint(cls, saved):
        value = copy.deepcopy(saved)
        fingerprint = value.pop('sha256')
        if value['schema']!='ag02.augmented.checkpoint.1' or digest(value)!=fingerprint:
            raise ValueError('Augmented checkpoint schema/hash mismatch')
        result = cls(MarketConfig(**value['market']), LearningConfig(**value['learning']), value['seed'])
        result.completed = integer(value['completed'], 'completed')
        if result.completed>result.learning.episodes or len(value['rows'])!=result.completed:
            raise ValueError('Checkpoint episode count mismatch')
        augmented_hash(value['q'])
        result.agent.q[:] = value['q']
        visits = np.asarray(value['visits'])
        if visits.shape!=SHAPE or (visits<0).any() or visits.sum()!=result.completed*result.market.steps:
            raise ValueError('Checkpoint visits mismatch')
        result.visits[:] = visits
        result.rows, result.trace = value['rows'], value['trace']
        result.env.demand_rng.bit_generator.state = value['rng']['demand']
        for rng, state in zip(result.env.sales_rngs, value['rng']['sales'], strict=True):
            rng.bit_generator.state = state
        result.agent.rng.bit_generator.state = value['rng']['agent']
        return result
