"""Independent tabular Q-learning maze, adapted in purpose from source [4].

Maze, actions, rewards and learning schedule follow the confirmed tutorial.
Implementation is written for this assignment with bounded episodes, a fixed RNG
seed, explicit terminal updates, strict greedy evaluation and a separate BFS check.
"""

from collections import deque

import numpy as np

MAZE = np.array([
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 0, 1, 1],
    [1, 0, 1, 0, 0, 0, 0, 0, 1, 1],
    [1, 0, 1, 0, 1, 1, 1, 0, 1, 1],
    [1, 0, 1, 0, 1, 0, 0, 0, 1, 1],
    [1, 0, 1, 0, 1, 0, 1, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1, 1, 0, 0],
], dtype=np.int8)
START, GOAL = (0, 0), (9, 9)
ACTIONS = ((0, -1), (0, 1), (-1, 0), (1, 0))


def valid(maze, state):
    row, col = state
    return bool(0 <= row < maze.shape[0] and 0 <= col < maze.shape[1] and maze[state] == 0)


def transition(maze, state, action, goal):
    delta = ACTIONS[action]
    following = (state[0] + delta[0], state[1] + delta[1])
    if not valid(maze, following):
        return state, -10, True
    if following == goal:
        return following, 50, True
    return following, -1, False


def choose_action(q, state, epsilon, rng):
    if not 0 <= epsilon <= 1:
        raise ValueError("epsilon must be between zero and one")
    if rng.random() < epsilon:
        return int(rng.integers(4))
    return int(np.argmax(q[state]))


def update_q(q, state, action, following, reward, done, alpha=0.1, gamma=0.9):
    future = 0.0 if done else float(np.max(q[following]))
    old = q[state + (action,)]
    q[state + (action,)] = old + alpha * (reward + gamma * future - old)


def train(maze=MAZE, start=START, goal=GOAL, episodes=5000, seed=42, max_steps=400):
    if episodes <= 0 or max_steps <= 0 or not valid(maze, start) or not valid(maze, goal):
        raise ValueError("Positive budgets and valid endpoints are required")
    rng = np.random.default_rng(seed)
    q = np.zeros(maze.shape + (4,), dtype=np.float64)
    epsilon = 0.5
    returns, lengths, successes = [], [], []
    truncated = 0
    for _ in range(episodes):
        state, total, reached = start, 0, False
        for step in range(1, max_steps + 1):
            action = choose_action(q, state, epsilon, rng)
            following, reward, done = transition(maze, state, action, goal)
            update_q(q, state, action, following, reward, done)
            state, total = following, total + reward
            if done:
                reached = state == goal
                break
        else:
            truncated += 1
        returns.append(total)
        lengths.append(step)
        successes.append(reached)
        epsilon = max(0.01, epsilon * 0.995)
    return {"q": q, "returns": np.array(returns), "lengths": np.array(lengths),
            "successes": np.array(successes), "truncated": truncated, "epsilon": epsilon}


def greedy_path(maze, q, start, goal, max_steps=200):
    path, visited = [start], {start}
    for _ in range(max_steps):
        if path[-1] == goal:
            return path, "goal"
        following, _, done = transition(maze, path[-1], int(np.argmax(q[path[-1]])), goal)
        if done and following != goal:
            return path, "collision"
        if following in visited:
            return path, "loop"
        path.append(following)
        visited.add(following)
    return path, "goal" if path[-1] == goal else "step_limit"


def shortest_path(maze, start, goal):
    pending, parent = deque([start]), {start: None}
    while pending:
        state = pending.popleft()
        if state == goal:
            path = []
            while state is not None:
                path.append(state)
                state = parent[state]
            return path[::-1]
        for delta in ACTIONS:
            following = (state[0] + delta[0], state[1] + delta[1])
            if valid(maze, following) and following not in parent:
                parent[following] = state
                pending.append(following)
    return []


def valid_path(maze, path):
    if not path or not all(valid(maze, state) for state in path):
        return False
    return all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(path, path[1:]))  # noqa: RUF007 -- show adjacent pairs explicitly
