"""Matched exogenous scenarios, frozen Q copy, and separate evaluation tie RNG."""

import numpy as np

from ..controlled import LearningConfig, MarketEnv, QAgent, RuleAgent, Tape, binary, integer
from ..training import q_digest


def evaluate_dev(q, market, *, episodes, scenario_seed, role=0, partition='development'):
    if partition not in {'fixture', 'development'}:
        raise PermissionError('Final evaluation requires the later declared evaluator/gate')
    integer(episodes, 'episodes', 1)
    binary(role, 'role')
    integer(scenario_seed, 'scenario_seed')
    if episodes > 100:
        raise ValueError('Phase 2 DEV evaluation is limited to 100 episodes')
    before = q_digest(q)
    learner = QAgent(LearningConfig(), int(np.random.SeedSequence([scenario_seed, 4]).generate_state(1)[0]))
    learner.q[:] = q
    learner.q.flags.writeable = False
    rule = RuleAgent()
    env = MarketEnv(market, scenario_seed)
    totals, action_counts, rows = np.zeros(2), np.zeros((2, 2), dtype=np.int64), []
    for episode in range(episodes):
        states = env.reset(Tape.generate(market, scenario_seed, episode))
        reward = np.zeros(2)
        for _ in range(market.steps):
            actions = [0, 0]
            actions[role] = learner.act(states[role], 0, explore=False)
            actions[1-role] = rule.act(states[1-role])
            result = env.step(actions)
            reward += result.rewards
            for index in range(2):
                action_counts[index, actions[index]] += 1
            states = result.states
        totals += reward
        rows.append({'episode': episode+1, 'learner_reward': float(reward[role]),
                     'rule_reward': float(reward[1-role])})
    after = q_digest(q)
    if before != after or q_digest(learner.q) != before:
        raise RuntimeError('Frozen Q changed during evaluation')
    return {'partition': partition, 'role': role, 'scenario_seed': scenario_seed,
            'episodes': episodes, 'steps': episodes * market.steps, 'rows': rows,
            'total_reward': float(totals[role]), 'mean_reward': float(totals[role] / (episodes * market.steps)),
            'rule_total_reward': float(totals[1-role]),
            'learner_action_counts': action_counts[role].tolist(), 'q_hash_before': before,
            'q_hash_after': after, 'exploration': False, 'tie_break': 'seeded_np_isclose_1e-5_1e-8'}
