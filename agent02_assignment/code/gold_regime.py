"""Causal calendar-adjacent TRAIN-only price direction, used solely as a demand proxy."""

import re
from itertools import pairwise

import numpy as np


def month_number(value):
    match = re.fullmatch(r'(\d{4})[-M](\d{2})', str(value))
    if not match or not 1 <= int(match[2]) <= 12:
        raise ValueError('Expected YYYY-MM or YYYYMmm calendar month')
    return int(match[1])*12+int(match[2])-1


def month_name(number):
    return f'{number//12:04d}-{number%12+1:02d}'


def prefix_records(rows, column, cutoff):
    """Stop on first later calendar label before accessing its price field."""
    result = []
    for row in rows:
        if not re.fullmatch(r'\d{4}M\d{2}', str(row[0])):
            continue
        number = month_number(row[0])
        if number > month_number(cutoff):
            break
        result.append((month_name(number), row[column]))
    return result


def estimate_regimes(rows):
    if len(rows) < 2:
        raise ValueError('Require a nontrivial TRAIN history')
    numbers = [month_number(row[0]) for row in rows]
    if any(b <= a for a, b in pairwise(numbers)):
        raise ValueError('Months must be unique and strictly increasing')
    valid = [isinstance(price, (int, float)) and not isinstance(price, bool)
             and np.isfinite(price) and price > 0 for _, price in rows]
    regimes, counts = [], np.zeros((2, 2), dtype=np.int64)
    for i in range(1, len(rows)):
        if numbers[i] == numbers[i-1]+1 and valid[i] and valid[i-1]:
            regimes.append({'month': rows[i][0], 'regime': int(rows[i][1] > rows[i-1][1])})
    if not regimes:
        raise ValueError('No adjacent valid price pair')
    for previous, following in pairwise(regimes):
        if month_number(following['month']) == month_number(previous['month'])+1:
            counts[previous['regime'], following['regime']] += 1
    prices = np.array([p for (_, p), ok in zip(rows, valid, strict=True) if ok], dtype=float)
    missing = [month_name(n) for n in range(numbers[0], numbers[-1]+1) if n not in set(numbers)]
    return {'kernel': ((counts+1)/(counts.sum(axis=1, keepdims=True)+2)).tolist(),
            'transition_counts': counts.tolist(), 'smoothing_pseudocount': 1,
            'regime_counts': np.bincount([r['regime'] for r in regimes], minlength=2).tolist(),
            'regimes': regimes, 'records': [{'month': m, 'gold_usd_per_troy_ounce': p}
                                           for (m, p), ok in zip(rows, valid, strict=True) if ok],
            'first_month': rows[0][0], 'last_month': rows[-1][0], 'observed_months': len(rows),
            'valid_prices': int(sum(valid)), 'invalid_price_months': [m for (m, _), ok in zip(rows, valid, strict=True) if not ok],
            'missing_months': missing, 'gap_pairs_excluded': sum(b != a+1 for a, b in pairwise(numbers)),
            'price_summary': {'minimum': float(prices.min()), 'maximum': float(prices.max()),
                              'mean': float(prices.mean()), 'median': float(np.median(prices)),
                              'std_ddof1': float(prices.std(ddof=1)) if len(prices) > 1 else None},
            'real_demand_measurement': False, 'initial_demand': 'Bernoulli(0.5)',
            'interpretation': 'Historical price direction calibrates a synthetic demand kernel; no demand causality or investment validation'}
