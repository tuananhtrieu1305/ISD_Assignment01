"""Model law and fair-RNG contracts, declared before implementation."""

from dataclasses import replace

import numpy as np
import pytest

from agent02_assignment.code.controlled import (
    LearningConfig,
    MarketConfig,
    MarketEnv,
    QAgent,
    RuleAgent,
    Tape,
    conversion,
    margin,
)


@pytest.mark.parametrize('field,value', [('steps', 0), ('price', float('nan')), ('cost', -1),
                                       ('discount', 1.1), ('customers_low', True), ('customers_high', 0),
                                       ('kernel', ((.8, .8), (.5, .5)))])
def test_bad_market_config_is_rejected(field, value):
    with pytest.raises(ValueError):
        replace(MarketConfig(), **{field: value})


@pytest.mark.parametrize('kwargs', [{'alpha': 0}, {'gamma': 1.1}, {'epsilon_start': -.1},
                                    {'epsilon_min': .3}, {'epsilon_decay': 0}, {'episodes': 0}])
def test_bad_learning_config_is_rejected(kwargs):
    with pytest.raises(ValueError):
        LearningConfig(**kwargs)


def test_schedule_and_fixed_epsilon_match_declaration():
    default = LearningConfig()
    assert default.epsilon_at(0) == .2
    assert default.epsilon_at(10) == pytest.approx(.2 * .995 ** 10)
    assert default.epsilon_at(4999) == .02
    fixed = LearningConfig(epsilon_start=.05, epsilon_min=.05, epsilon_decay=1)
    assert fixed.epsilon_at(0) == fixed.epsilon_at(4999) == .05
    with pytest.raises(ValueError):
        default.epsilon_at(-1)


@pytest.mark.parametrize('demand', [0, 1])
@pytest.mark.parametrize('own', [0, 1])
@pytest.mark.parametrize('other', [0, 1])
def test_conversion_table_and_margin(demand, own, other):
    assert conversion(demand, own, other) == pytest.approx(.30 + .25*demand + .15*own - .10*other)
    assert margin(MarketConfig(), own) == (3 if own else 5)


@pytest.mark.parametrize('state,expected', [((0, 0), 0), ((0, 1), 0), ((1, 0), 0), ((1, 1), 1)])
def test_rule_has_exact_reference_policy(state, expected):
    agent = RuleAgent()
    assert agent.act(state) == expected
    assert not hasattr(agent, 'q') and not hasattr(agent, 'learn')


def test_q_question_three_and_terminal_are_correct():
    agent = QAgent(LearningConfig(), seed=123)
    agent.q[0, 0, 0] = 4
    agent.q[1, 1] = [3, 5]
    agent.learn((0, 0), 0, 6, (1, 1), terminal=False)
    assert agent.q[0, 0, 0] == pytest.approx(4.65)
    agent.q[0, 0, 0] = 4
    agent.learn((0, 0), 0, 6, (1, 1), terminal=True)
    assert agent.q[0, 0, 0] == pytest.approx(4.2)


def test_q_only_updates_selected_entry():
    agent = QAgent(LearningConfig(), seed=123)
    agent.learn((1, 0), 1, 10, (0, 0), terminal=True)
    assert np.count_nonzero(agent.q) == 1 and agent.q[1, 0, 1] == 1


def test_exploration_and_tie_breaking_are_seeded_and_not_argmax_zero():
    left = QAgent(LearningConfig(), seed=123)
    right = QAgent(LearningConfig(), seed=123)
    actions = [left.act((0, 0), .0) for _ in range(100)]
    assert actions == [right.act((0, 0), .0) for _ in range(100)]
    assert set(actions) == {0, 1}
    left.q[0, 0] = [0, 100]
    assert {left.act((0, 0), 0) for _ in range(20)} == {1}
    assert {left.act((0, 0), 1) for _ in range(100)} == {0, 1}


@pytest.mark.parametrize('state', [(2, 0), (0,), (False, 1), (-1, 1)])
def test_agent_rejects_invalid_local_state(state):
    with pytest.raises(ValueError):
        RuleAgent().act(state)


def test_nonfinite_reward_and_invalid_action_are_rejected():
    agent = QAgent(LearningConfig(), seed=1)
    with pytest.raises(ValueError):
        agent.learn((0, 0), 2, 1, (0, 0), terminal=True)
    with pytest.raises(ValueError):
        agent.learn((0, 0), 0, float('nan'), (0, 0), terminal=True)
    with pytest.raises(ValueError):
        agent.act((0, 0), 2)


def test_environment_uses_simultaneous_actions_and_previous_history():
    model = MarketConfig(steps=2)
    env = MarketEnv(model, seed=123)
    tape = Tape(demand=(1, 0, 1), uniforms=np.zeros((2, 2, 20)))
    assert env.reset(tape) == ((1, 0), (1, 0))
    result = env.step((1, 0))
    assert result.probabilities == pytest.approx((.7, .45))
    assert result.sales == (20, 20) and result.rewards == (60, 100)
    assert result.states == ((0, 0), (0, 1))
    assert result.done is False
    final = env.step((0, 1))
    assert final.states == ((1, 1), (1, 0)) and final.done is True
    assert final.rewards == (50, 30)
    with pytest.raises(RuntimeError):
        env.step((0, 0))


@pytest.mark.parametrize('demand', [0, 1])
@pytest.mark.parametrize('actions', [(0, 0), (0, 1), (1, 0), (1, 1)])
def test_all_joint_actions_use_same_snapshot_and_profit_law(demand, actions):
    config = MarketConfig(steps=1)
    env = MarketEnv(config, seed=1)
    env.reset(Tape(demand=(demand, 0), uniforms=np.zeros((1, 2, 20))))
    result = env.step(actions)
    customers = 20 if demand else 10
    for role in (0, 1):
        assert result.probabilities[role] == pytest.approx(conversion(demand, actions[role], actions[1-role]))
        assert result.rewards[role] == customers * margin(config, actions[role])


@pytest.mark.parametrize('actions', [(0,), (0, 2), (True, 1), (0, float('nan'))])
def test_environment_rejects_actions_before_mutation(actions):
    env = MarketEnv(MarketConfig(), seed=1)
    before = env.reset()
    with pytest.raises(ValueError):
        env.step(actions)
    assert env.states() == before and env.elapsed == 0


def test_step_requires_reset_and_reset_clears_history():
    env = MarketEnv(MarketConfig(steps=1), seed=1)
    with pytest.raises(RuntimeError):
        env.step((0, 0))
    env.reset()
    env.step((1, 1))
    reset = env.reset()
    assert reset[0][1] == reset[1][1] == 0 and env.elapsed == 0


def test_tapes_are_immutable_seeded_and_independent_of_policy():
    config = MarketConfig()
    left = Tape.generate(config, scenario_seed=910001, episode=0)
    same = Tape.generate(config, scenario_seed=910001, episode=0)
    other = Tape.generate(config, scenario_seed=910001, episode=1)
    assert left.demand == same.demand
    np.testing.assert_array_equal(left.uniforms, same.uniforms)
    assert not np.array_equal(left.uniforms, other.uniforms)
    with pytest.raises(ValueError):
        left.uniforms[0, 0, 0] = .3
    env1, env2 = MarketEnv(config, 1), MarketEnv(config, 999)
    env1.reset(left)
    env2.reset(left)
    for index in range(config.steps):
        assert env1.step((0, 0)).states[0][0] == env2.step((1, 1)).states[0][0] == left.demand[index+1]


def test_online_demand_rng_is_not_affected_by_sales_or_actions():
    first, second = MarketEnv(MarketConfig(), 7), MarketEnv(MarketConfig(), 7)
    assert first.reset() == second.reset()
    for _ in range(20):
        assert first.step((0, 0)).states[0][0] == second.step((1, 1)).states[0][0]


def test_tape_sales_have_binomial_marginals():
    tape = Tape.generate(MarketConfig(steps=20000, customers_high=10), scenario_seed=12, episode=0)
    samples = (tape.uniforms[:, 0, :10] < .3).sum(axis=1)
    assert abs(samples.mean() - 3) < .05
    assert abs(samples.var() - 2.1) < .07


def test_tape_validation_does_not_accept_wrong_shapes_or_probability_values():
    with pytest.raises(ValueError):
        Tape(demand=(0, 2), uniforms=np.zeros((1, 2, 20)))
    with pytest.raises(ValueError):
        Tape(demand=(0, 1), uniforms=np.zeros((1, 1, 20)))
    with pytest.raises(ValueError):
        Tape(demand=(0, 1), uniforms=np.full((1, 2, 20), np.nan))
