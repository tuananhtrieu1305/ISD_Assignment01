"""Frozen 320-value policy on the same exogenous demand/customer tapes as Phase5/6."""

import numpy as np

from ..augmented import AugmentedAgent, augmented_hash, observe, state_index
from ..controlled import LearningConfig, MarketEnv, RuleAgent, Tape
from .final_v1 import budget


def evaluate_augmented(q, market, *, episodes, scenario_seed, role, guard=None):
    budget(episodes, role)
    if market.steps!=20:
        raise ValueError('Scientific augmented evaluation uses registered20-step horizon')
    before = augmented_hash(q)
    agent = AugmentedAgent(LearningConfig(), int(np.random.SeedSequence([scenario_seed,4]).generate_state(1)[0]))
    agent.q[:] = q
    agent.q.flags.writeable = False
    env, rule = MarketEnv(market, scenario_seed), RuleAgent()
    rows, trace = [], []
    counts, visits, totals = np.zeros((2,2),dtype=np.int64), np.zeros(160,dtype=np.int64), np.zeros(2)
    for episode in range(episodes):
        if guard is not None:
            guard()
        states = env.reset(Tape.generate(market, scenario_seed, episode))
        reward, action_counts, state_visits = np.zeros(2), np.zeros((2,2),dtype=np.int64), np.zeros(160,dtype=np.int64)
        for step in range(market.steps):
            observation = observe(env, role)
            actions = [0,0]
            actions[role] = agent.act(observation, 0, explore=False)
            actions[1-role] = rule.act(states[1-role])
            state_visits[np.ravel_multi_index(state_index(observation), (2,2,2,20))] += 1
            result = env.step(actions)
            reward += result.rewards
            for i in (0,1):
                action_counts[i,actions[i]] += 1
            if len(trace)<20:
                trace.append({'episode':episode+1, 'step':step+1, 'augmented_state':list(observation),
                    'states': [list(s) for s in states], 'actions_physical_roles': actions,
                    'rewards_physical_roles':list(result.rewards)})
            states = result.states
        rows.append({'episode':episode+1, 'learner_reward':float(reward[role]), 'opponent_reward':float(reward[1-role]),
            'learner_action_counts':action_counts[role].tolist(), 'opponent_action_counts':action_counts[1-role].tolist(),
            'state_visits':state_visits.tolist()})
        counts += action_counts
        visits += state_visits
        totals += reward
    if augmented_hash(q)!=before or augmented_hash(agent.q)!=before:
        raise RuntimeError('Frozen augmented Q changed')
    return {'engine':'augmented_matched_tapes_v1', 'policy_kind':'augmented', 'policy_sha256':before,
        'episodes':episodes, 'steps':episodes*market.steps, 'role':role, 'scenario_seed':scenario_seed,
        'total_reward':float(totals[role]), 'mean_reward':float(totals[role]/(episodes*market.steps)),
        'opponent_total_reward':float(totals[1-role]), 'opponent_mean_reward':float(totals[1-role]/(episodes*market.steps)),
        'learner_action_counts':counts[role].tolist(), 'opponent_action_counts':counts[1-role].tolist(),
        'state_visits':visits.tolist(), 'state_visits_axis_order':['demand','own_previous','competitor_previous','remaining_minus1'],
        'rows':rows, 'trace_sample':trace, 'q_hash_before':before, 'q_hash_after':augmented_hash(q),
        'exploration':False, 'tie_break':'seeded_np_isclose_rtol1e-5_atol1e-8; same evaluation tie RNG channel4 as baselines'}
