"""Episode-boundary instrumentation around unchanged teacher classes and RNG order."""

import copy

import numpy as np

from .controlled import LearningConfig, MarketConfig, integer
from .reference_adapter import load_reference
from .training import digest, q_digest


class ReferenceSession:
    """Same loop/calls as train_rl_against_rule; added logging makes no RNG draws."""

    def __init__(self, market, learning, seed):
        if market != MarketConfig():
            raise ValueError('REF adapter only supports the unchanged teaching market')
        self.market, self.learning, self.seed = market, learning, integer(seed, 'seed')
        teacher = load_reference()
        self.config = teacher.Config(episodes=learning.episodes, alpha=learning.alpha, gamma=learning.gamma,
                                     epsilon_start=learning.epsilon_start, epsilon_min=learning.epsilon_min,
                                     epsilon_decay=learning.epsilon_decay)
        self.env = teacher.ECommerceEnvironment(self.config, seed=seed)
        self.agent = teacher.QLearningAgent(alpha=learning.alpha, gamma=learning.gamma,
                                            epsilon=learning.epsilon_start, seed=seed+10000)
        self.rule = teacher.RuleBasedAgent()
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
            self.agent.epsilon = self.learning.epsilon_at(self.completed)
            states = self.env.reset()
            totals = [0., 0.]
            counts = np.zeros((2, 2), dtype=np.int64)
            for step in range(self.market.steps):
                actions = [self.agent.act(states[0], explore=True), self.rule.act(states[1])]
                next_states, rewards, info = self.env.step(actions)
                terminal = step == self.market.steps - 1
                self.agent.learn(state=states[0], action=actions[0], reward=rewards[0],
                                 next_state=next_states[0], terminal=terminal)
                self.visits[(*states[0], actions[0])] += 1
                for role in (0, 1):
                    totals[role] += rewards[role]
                    counts[role, actions[role]] += 1
                if len(self.trace) < trace_limit:
                    self.trace.append({'episode': self.completed+1, 'step': step+1,
                                       'states_before': [list(s) for s in states], 'actions': actions,
                                       'rewards': rewards, 'states_after': [list(s) for s in next_states],
                                       'sales': info['sales'], 'terminal': terminal})
                states = next_states
            self.completed += 1
            self.rows.append({'episode': self.completed, 'rl_episode_reward': totals[0],
                              'rule_episode_reward': totals[1],
                              'rl_mean_reward_per_step': totals[0]/self.market.steps,
                              'rule_mean_reward_per_step': totals[1]/self.market.steps,
                              'epsilon': self.agent.epsilon, 'alpha': self.learning.alpha,
                              'action_counts': counts.tolist()})

    def checkpoint(self):
        from dataclasses import asdict

        state = {'schema': 'ag02.reference.checkpoint.1', 'market': asdict(self.market),
                 'learning': asdict(self.learning), 'seed': self.seed, 'completed': self.completed,
                 'q': self.agent.q.tolist(), 'rows': self.rows, 'trace': self.trace,
                 'visits': self.visits.tolist(), 'epsilon': self.agent.epsilon,
                 'rng': {'environment': self.env.rng.bit_generator.state,
                         'agent': self.agent.rng.bit_generator.state}}
        return copy.deepcopy({**state, 'sha256': digest(state)})

    @classmethod
    def from_checkpoint(cls, saved):
        state = copy.deepcopy(saved)
        fingerprint = state.pop('sha256')
        if state['schema'] != 'ag02.reference.checkpoint.1' or digest(state) != fingerprint:
            raise ValueError('REF checkpoint schema/hash mismatch')
        result = cls(MarketConfig(**state['market']), LearningConfig(**state['learning']), state['seed'])
        result.completed = integer(state['completed'], 'completed')
        if result.completed > result.learning.episodes or len(state['rows']) != result.completed:
            raise ValueError('REF checkpoint count mismatch')
        q_digest(state['q'])
        result.agent.q[:] = state['q']
        visits = np.asarray(state['visits'])
        if visits.shape != (2, 2, 2) or (visits < 0).any() or visits.sum() != result.completed * result.market.steps:
            raise ValueError('REF checkpoint visitation mismatch')
        result.visits[:] = visits
        result.rows, result.trace = state['rows'], state['trace']
        result.agent.epsilon = state['epsilon']
        result.env.rng.bit_generator.state = state['rng']['environment']
        result.agent.rng.bit_generator.state = state['rng']['agent']
        return result
