"""Finite-horizon known-model checks against fixed RuleAgent. Never supplies training labels."""

from itertools import product

import numpy as np

from .augmented import SHAPE, augmented_hash
from .controlled import RuleAgent, conversion, margin
from .training import q_digest


def backward(market, gamma, choose):
    if not np.isfinite(gamma) or not 0<=gamma<=1 or market.steps>20:
        raise ValueError('Invalid oracle gamma or horizon')
    q = np.zeros(SHAPE)
    value = np.zeros((2,2,2,21))
    rule = RuleAgent()
    for remaining in range(1,market.steps+1):
        for d,own,other in product((0,1),repeat=3):
            opponent = rule.act((d,own))
            customers = market.customers_high if d else market.customers_low
            for action in (0,1):
                reward = customers*conversion(d,action,opponent)*margin(market,action)
                future = sum(market.kernel[d][following]*value[following,action,opponent,remaining-1] for following in (0,1))
                q[d,own,other,remaining-1,action] = reward+gamma*future
            values = q[d,own,other,remaining-1]
            actions = choose(d,own,other,remaining,values)
            value[d,own,other,remaining] = float(np.mean(values[actions]))
    return {'q':q,'value':value,'gamma':gamma,'reset_expected_return':float(value[:,0,0,market.steps].mean()),
            'scope':'known simulator/fixed rule/initial demandBernoulli0.5; exact expectation, not sampled final or learned oracle'}


def solve(market, *, gamma=1.):
    return backward(market,gamma,lambda d,own,other,remaining,values: np.flatnonzero(
        np.isclose(values,values.max(),rtol=0,atol=1e-12)))


def policy_value(market, *, q=None, kind='rule', gamma=1.):
    if kind not in ('rule','partial','augmented'):
        raise ValueError('Unknown oracle policy kind')
    if kind=='augmented':
        augmented_hash(q)
    elif kind=='partial':
        q_digest(q)
    array = np.asarray(q) if q is not None else None
    rule = RuleAgent()
    def choose(d,own,other,remaining,values):
        if kind=='rule':
            return [rule.act((d,other))]
        values = array[d,other] if kind=='partial' else array[d,own,other,remaining-1]
        return np.flatnonzero(np.isclose(values,values.max(),rtol=1e-5,atol=1e-8))
    return backward(market,gamma,choose)
