"""Teaching market and tabular policies; CONTROLLED v1 uses separate random streams."""

from dataclasses import dataclass
from numbers import Integral

import numpy as np


def integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return int(value)


def binary(value, name='binary value'):
    result = integer(value, name)
    if result > 1:
        raise ValueError(f'{name} must be 0 or 1')
    return result


def state_pair(state):
    if not isinstance(state, (tuple, list)) or len(state) != 2:
        raise ValueError('Local state must contain demand and competitor previous action')
    return tuple(binary(value) for value in state)


@dataclass(frozen=True)
class MarketConfig:
    steps: int = 20
    price: float = 10.0
    cost: float = 5.0
    discount: float = .20
    customers_low: int = 10
    customers_high: int = 20
    kernel: tuple = ((.5, .5), (.5, .5))

    def __post_init__(self):
        for name in ('steps', 'customers_low', 'customers_high'):
            integer(getattr(self, name), name, 1)
        values = [self.price, self.cost, self.discount]
        if not np.isfinite(values).all() or self.price <= 0 or self.cost < 0 or not 0 <= self.discount <= 1:
            raise ValueError('Invalid price, cost or discount')
        kernel = np.asarray(self.kernel, dtype=float)
        if (kernel.shape != (2, 2) or not np.isfinite(kernel).all() or (kernel < 0).any()
                or not np.allclose(kernel.sum(axis=1), 1, rtol=0, atol=1e-12)):
            raise ValueError('Demand kernel must be a 2x2 stochastic matrix')
        object.__setattr__(self, 'kernel', tuple(tuple(float(x) for x in row) for row in kernel))


@dataclass(frozen=True)
class LearningConfig:
    episodes: int = 5000
    alpha: float = .10
    gamma: float = .90
    epsilon_start: float = .20
    epsilon_min: float = .02
    epsilon_decay: float = .995

    def __post_init__(self):
        integer(self.episodes, 'episodes', 1)
        if (not np.isfinite([self.alpha, self.gamma, self.epsilon_start,
                             self.epsilon_min, self.epsilon_decay]).all()
                or not 0 < self.alpha <= 1 or not 0 <= self.gamma <= 1
                or not 0 <= self.epsilon_min <= self.epsilon_start <= 1
                or not 0 < self.epsilon_decay <= 1):
            raise ValueError('Invalid learning parameters')

    def epsilon_at(self, episode):
        integer(episode, 'episode')
        return max(self.epsilon_min, self.epsilon_start * self.epsilon_decay ** episode)


def conversion(demand, own_action, other_action):
    d, own, other = binary(demand), binary(own_action), binary(other_action)
    return float(np.clip(.30 + .25*d + .15*own - .10*other, .05, .95))


def margin(config, action):
    return config.price * (1 - config.discount * binary(action)) - config.cost


@dataclass(frozen=True)
class Tape:
    """One episode of exogenous demand and independent customer uniforms, not sales."""
    demand: tuple
    uniforms: np.ndarray

    def __post_init__(self):
        demand = tuple(binary(d) for d in self.demand)
        uniforms = np.array(self.uniforms, dtype=np.float64, copy=True)
        if (len(demand) < 2 or uniforms.ndim != 3 or uniforms.shape[:2] != (len(demand)-1, 2)
                or uniforms.shape[2] < 1 or not np.isfinite(uniforms).all()
                or (uniforms < 0).any() or (uniforms >= 1).any()):
            raise ValueError('Malformed scenario tape')
        uniforms.flags.writeable = False
        object.__setattr__(self, 'demand', demand)
        object.__setattr__(self, 'uniforms', uniforms)

    @classmethod
    def generate(cls, config, scenario_seed, episode):
        integer(scenario_seed, 'scenario_seed')
        integer(episode, 'episode')
        demand_rng = np.random.default_rng(np.random.SeedSequence([scenario_seed, episode, 0]))
        sales_rng = np.random.default_rng(np.random.SeedSequence([scenario_seed, episode, 1]))
        demand = [int(demand_rng.integers(2))]
        for _ in range(config.steps):
            demand.append(int(demand_rng.random() >= config.kernel[demand[-1]][0]))
        uniforms = sales_rng.random((config.steps, 2, max(config.customers_low, config.customers_high)))
        return cls(tuple(demand), uniforms)


@dataclass(frozen=True)
class StepResult:
    states: tuple
    rewards: tuple
    sales: tuple
    probabilities: tuple
    customers: int
    done: bool


class MarketEnv:
    def __init__(self, config, seed):
        self.config = config
        integer(seed, 'seed')
        self.demand_rng = np.random.default_rng(np.random.SeedSequence([seed, 0]))
        self.sales_rngs = [np.random.default_rng(np.random.SeedSequence([seed, index])) for index in (1, 2)]
        self.demand, self.previous, self.elapsed = 0, (0, 0), 0
        self.ready, self.tape = False, None

    def states(self):
        return ((self.demand, self.previous[1]), (self.demand, self.previous[0]))

    def reset(self, tape=None):
        if tape is not None and tape.uniforms.shape != (
                self.config.steps, 2, max(self.config.customers_low, self.config.customers_high)):
            raise ValueError('Tape dimensions do not match market configuration')
        self.tape = tape
        self.demand = tape.demand[0] if tape is not None else int(self.demand_rng.integers(2))
        self.previous, self.elapsed, self.ready = (0, 0), 0, True
        return self.states()

    def step(self, actions):
        if not self.ready or self.elapsed >= self.config.steps:
            raise RuntimeError('Call reset before stepping or after the episode ends')
        if not isinstance(actions, (tuple, list)) or len(actions) != 2:
            raise ValueError('Exactly two simultaneous actions are required')
        actions = tuple(binary(action, 'action') for action in actions)
        customers = self.config.customers_high if self.demand else self.config.customers_low
        probabilities = tuple(conversion(self.demand, actions[i], actions[1-i]) for i in range(2))
        if self.tape is None:
            sales = tuple(int(self.sales_rngs[i].binomial(customers, probabilities[i])) for i in range(2))
            next_demand = int(self.demand_rng.random() >= self.config.kernel[self.demand][0])
        else:
            sales = tuple(int((self.tape.uniforms[self.elapsed, i, :customers] < probabilities[i]).sum())
                          for i in range(2))
            next_demand = self.tape.demand[self.elapsed+1]
        rewards = tuple(sales[i] * margin(self.config, actions[i]) for i in range(2))
        self.previous, self.demand = actions, next_demand
        self.elapsed += 1
        return StepResult(self.states(), rewards, sales, probabilities, customers,
                          self.elapsed == self.config.steps)


class RuleAgent:
    def act(self, state):
        demand, competitor_previous = state_pair(state)
        return int(demand == 1 and competitor_previous == 1)


class QAgent:
    def __init__(self, config, seed):
        self.config = config
        integer(seed, 'seed')
        self.rng = np.random.default_rng(seed)
        self.q = np.zeros((2, 2, 2), dtype=np.float64)

    def act(self, state, epsilon, *, explore=True):
        state = state_pair(state)
        if not np.isfinite(epsilon) or not 0 <= epsilon <= 1:
            raise ValueError('epsilon must be in [0,1]')
        values = self.q[state]
        if not np.isfinite(values).all():
            raise ValueError('Nonfinite Q values')
        if explore and self.rng.random() < epsilon:
            return int(self.rng.integers(2))
        # Same near-tie convention as the reference, made explicit in the protocol.
        best = np.flatnonzero(np.isclose(values, values.max(), rtol=1e-5, atol=1e-8))
        return int(self.rng.choice(best))

    def learn(self, state, action, reward, following, terminal):
        state, following, action = state_pair(state), state_pair(following), binary(action, 'action')
        if not np.isfinite(reward):
            raise ValueError('Nonfinite reward')
        target = reward if terminal else reward + self.config.gamma * float(self.q[following].max())
        key = (*state, action)
        self.q[key] += self.config.alpha * (target - self.q[key])
        if not np.isfinite(self.q[key]):
            raise ValueError('Nonfinite Q update')
