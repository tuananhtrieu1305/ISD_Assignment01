"""Frozen tabular evaluation on matched tapes; native teacher reference kept separate."""

import copy
from pathlib import Path

import numpy as np

from ...workspace import sha256_file
from ..controlled import LearningConfig, MarketEnv, QAgent, RuleAgent, Tape, binary, integer
from ..reference_adapter import load_reference
from ..training import digest, q_digest


def policy_hash(q, kind='q'):
    if kind == 'q':
        return q_digest(q)
    if kind not in ('rule', 'no_discount'):
        raise ValueError('Unknown frozen policy kind')
    return digest({'kind': kind, 'controlled_source_sha256': sha256_file(Path(__file__).parents[1]/'controlled.py')})


def budget(episodes, role):
    integer(episodes, 'episodes', 1)
    binary(role, 'role')
    if episodes > 500:
        raise ValueError('Maximum evaluation budget is 500 episodes per role')


def evaluate_tapes(q, market, *, episodes, scenario_seed, role, kind='q', guard=None):
    budget(episodes, role)
    fingerprint = policy_hash(q, kind)
    before = q_digest(q) if kind == 'q' else None
    learner = None
    if kind == 'q':
        learner = QAgent(LearningConfig(), int(np.random.SeedSequence([scenario_seed, 4]).generate_state(1)[0]))
        learner.q[:] = q
        learner.q.flags.writeable = False
    rule, env = RuleAgent(), MarketEnv(market, scenario_seed)
    rows, trace = [], []
    counts = np.zeros((2, 2), dtype=np.int64)
    visits = np.zeros(4, dtype=np.int64)
    totals = np.zeros(2)
    for episode in range(episodes):
        if guard is not None:
            guard()
        states = env.reset(Tape.generate(market, scenario_seed, episode))
        reward, episode_counts, episode_visits = np.zeros(2), np.zeros((2, 2), dtype=np.int64), np.zeros(4, dtype=np.int64)
        for step in range(market.steps):
            actions = [0, 0]
            actions[role] = learner.act(states[role], 0, explore=False) if kind == 'q' else (
                rule.act(states[role]) if kind == 'rule' else 0)
            actions[1-role] = rule.act(states[1-role])
            episode_visits[2*states[role][0]+states[role][1]] += 1
            result = env.step(actions)
            reward += result.rewards
            for physical in (0, 1):
                episode_counts[physical, actions[physical]] += 1
            if len(trace) < 20:
                trace.append({'episode': episode+1, 'step': step+1, 'states': [list(s) for s in states],
                              'actions_physical_roles': actions, 'rewards_physical_roles': list(result.rewards)})
            states = result.states
        rows.append({'episode': episode+1, 'learner_reward': float(reward[role]),
                     'opponent_reward': float(reward[1-role]),
                     'learner_action_counts': episode_counts[role].tolist(),
                     'opponent_action_counts': episode_counts[1-role].tolist(), 'state_visits': episode_visits.tolist()})
        counts += episode_counts
        visits += episode_visits
        totals += reward
    after = q_digest(q) if kind == 'q' else None
    if before != after or (learner is not None and q_digest(learner.q) != before):
        raise RuntimeError('Frozen Q changed')
    return {'engine': 'matched_tapes_v1', 'policy_kind': kind, 'policy_sha256': fingerprint,
            'episodes': episodes, 'steps': episodes*market.steps, 'role': role, 'scenario_seed': scenario_seed,
            'total_reward': float(totals[role]), 'mean_reward': float(totals[role]/(episodes*market.steps)),
            'opponent_total_reward': float(totals[1-role]),
            'opponent_mean_reward': float(totals[1-role]/(episodes*market.steps)),
            'learner_action_counts': counts[role].tolist(), 'opponent_action_counts': counts[1-role].tolist(),
            'state_visits': visits.tolist(), 'rows': rows, 'trace_sample': trace,
            'q_hash_before': before, 'q_hash_after': after, 'exploration': False,
            'tie_break': 'seeded_np_isclose_rtol1e-5_atol1e-8; evaluation RNG separate from train'}


def native_reference(q, policy_rng_state, *, episodes, scenario_seed, guard=None):
    budget(episodes, 0)
    teacher = load_reference()
    agent = teacher.QLearningAgent()
    agent.q[:] = q
    agent.q.flags.writeable = False
    agent.rng.bit_generator.state = copy.deepcopy(policy_rng_state)
    before, rng_before = q_digest(q), copy.deepcopy(agent.rng.bit_generator.state)
    episode_counts = np.zeros((episodes, 2, 2), dtype=np.int64)
    calls = [0, 0]
    original_act = agent.act
    def logged_act(state, explore=True):
        action = original_act(state, explore=explore)
        episode_counts[calls[0]//20, 0, action] += 1
        calls[0] += 1
        return action
    agent.act = logged_act
    original_rule, original_env = teacher.RuleBasedAgent, teacher.ECommerceEnvironment
    class LoggedRule(original_rule):
        def act(self, state):
            action = super().act(state)
            episode_counts[calls[1]//20, 1, action] += 1
            calls[1] += 1
            return action
    class GuardEnvironment(original_env):
        def reset(self):
            if guard is not None:
                guard()
            return super().reset()
    teacher.RuleBasedAgent, teacher.ECommerceEnvironment = LoggedRule, GuardEnvironment
    try:
        summary, native_rows = teacher.evaluate_pair(teacher.Config(), agent, episodes=episodes, seed=scenario_seed)
    finally:
        teacher.RuleBasedAgent, teacher.ECommerceEnvironment = original_rule, original_env
    rows = [{'episode': row['episode'], 'learner_reward': row['rl_reward'], 'opponent_reward': row['rule_reward'],
             'learner_action_counts': episode_counts[i, 0].tolist(),
             'opponent_action_counts': episode_counts[i, 1].tolist()} for i, row in enumerate(native_rows)]
    if q_digest(q) != before or q_digest(agent.q) != before:
        raise RuntimeError('Native reference Q changed')
    return {'engine': 'teacher_native_evaluate_pair', 'policy_kind': 'q', 'policy_sha256': before,
            'role': 0, 'scenario_seed': scenario_seed, 'episodes': episodes, 'steps': episodes*20,
            'rows': rows, 'total_reward': float(summary[0]['total_reward']),
            'mean_reward': float(summary[0]['mean_reward_per_step']),
            'opponent_total_reward': float(summary[1]['total_reward']),
            'opponent_mean_reward': float(summary[1]['mean_reward_per_step']),
            'learner_action_counts': episode_counts[:, 0].sum(axis=0).tolist(),
            'opponent_action_counts': episode_counts[:, 1].sum(axis=0).tolist(),
            'q_hash_before': before, 'q_hash_after': before, 'policy_rng_before': rng_before,
            'policy_rng_after': agent.rng.bit_generator.state, 'exploration': False,
            'tie_break': 'native original agent RNG copied from trained checkpoint; no exploration'}
