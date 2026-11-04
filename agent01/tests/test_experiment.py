import numpy as np
import pytest

from discovering_ai_agent import experiment as ex


@pytest.mark.parametrize("state,valid", [((0, 0), True), ((0, 1), False), ((-1, 0), False), ((10, 0), False), ((0, 10), False)])
def test_validity(state, valid):
    assert ex.valid(ex.MAZE, state) is valid


def test_wall_and_boundary_end_episode():
    for action in (0, 1, 2):
        state, reward, done = ex.transition(ex.MAZE, (0, 0), action, ex.GOAL)
        assert (state, reward, done) == ((0, 0), -10, True)


def test_step_and_goal_rewards():
    assert ex.transition(ex.MAZE, (0, 0), 3, ex.GOAL) == ((1, 0), -1, False)
    assert ex.transition(ex.MAZE, (9, 8), 1, ex.GOAL) == ((9, 9), 50, True)


def test_epsilon_greedy():
    q = np.zeros((10, 10, 4))
    q[0, 0, 3] = 9
    rng = np.random.default_rng(7)
    assert ex.choose_action(q, (0, 0), 0, rng) == 3
    assert len({ex.choose_action(q, (0, 0), 1, rng) for _ in range(100)}) == 4


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_invalid_epsilon(value):
    with pytest.raises(ValueError):
        ex.choose_action(np.zeros((10, 10, 4)), ex.START, value, np.random.default_rng(1))


def test_terminal_update_does_not_bootstrap():
    q = np.zeros((10, 10, 4))
    q[ex.GOAL] = 999
    ex.update_q(q, (9, 8), 1, ex.GOAL, 50, True)
    assert q[9, 8, 1] == 5


def test_nonterminal_update():
    q = np.zeros((10, 10, 4))
    q[1, 0, 2] = 10
    ex.update_q(q, ex.START, 3, (1, 0), -1, False)
    assert q[0, 0, 3] == pytest.approx(0.8)


def test_bfs_reference_and_unreachable():
    path = ex.shortest_path(ex.MAZE, ex.START, ex.GOAL)
    assert path[0] == ex.START and path[-1] == ex.GOAL
    assert ex.valid_path(ex.MAZE, path)
    assert ex.shortest_path(np.array([[0, 1, 0]]), (0, 0), (0, 2)) == []


def test_invalid_path():
    assert not ex.valid_path(ex.MAZE, [])
    assert not ex.valid_path(ex.MAZE, [(0, 0), (1, 1)])
    assert not ex.valid_path(ex.MAZE, [(0, 0), (0, 1)])


def test_greedy_collision_and_loop_are_reported():
    q = np.zeros((10, 10, 4))
    assert ex.greedy_path(ex.MAZE, q, ex.START, ex.GOAL)[1] == "collision"
    q[0, 0, 3] = 1
    q[1, 0, 2] = 1
    assert ex.greedy_path(ex.MAZE, q, ex.START, ex.GOAL)[1] == "loop"
    assert ex.greedy_path(ex.MAZE, q, ex.START, ex.GOAL, max_steps=1)[1] == "step_limit"


def test_seeded_training_reproducible_and_bounded():
    first = ex.train(episodes=20, max_steps=2)
    second = ex.train(episodes=20, max_steps=2)
    np.testing.assert_array_equal(first["q"], second["q"])
    assert np.all(first["lengths"] <= 2)
    assert first["truncated"] > 0


@pytest.mark.parametrize("kwargs", [{"episodes": 0}, {"max_steps": 0}, {"start": (0, 1)}, {"goal": (-1, 0)}])
def test_training_rejects_invalid_setup(kwargs):
    with pytest.raises(ValueError):
        ex.train(**kwargs)


def test_full_training_reaches_goal_and_matches_bfs():
    result = ex.train()
    path, status = ex.greedy_path(ex.MAZE, result["q"], ex.START, ex.GOAL)
    baseline = ex.shortest_path(ex.MAZE, ex.START, ex.GOAL)
    assert status == "goal"
    assert ex.valid_path(ex.MAZE, path)
    assert len(path) == len(baseline)
    assert result["epsilon"] == 0.01
    assert result["q"].shape == (10, 10, 4)
    assert result["truncated"] == 0
