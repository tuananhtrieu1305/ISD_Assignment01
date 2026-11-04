# Phase 15 experiment report

- TEST was executed exactly once after validation lock.
- Locked config SHA-256: `560c671a3920bd6bde9f7fc005f3c952f857c55969c989bb6109932623210c9e`.
- No claim of hallucination reduction is made; citation validity and unsupported-answer errors are reported.

## TEST summary

| Domain | Model | R@5 | MRR@10 | Token F1 | p95 ms |
|---|---:|---:|---:|---:|---:|
| medical | B0 | 0.403 | 0.250 | 0.186 | 2.43 |
| medical | B1 | 0.339 | 0.210 | 0.208 | 2.95 |
| medical | B2 | 0.403 | 0.232 | 0.193 | 6.47 |
| medical | B3 | 0.581 | 0.418 | 0.234 | 2.63 |
| medical | B4 | 0.581 | 0.418 | 0.234 | 6.90 |
| finance | B0 | 0.532 | 0.404 | 0.000 | 44.13 |
| finance | B1 | 0.232 | 0.162 | 0.000 | 56.29 |
| finance | B2 | 0.443 | 0.320 | 0.000 | 101.65 |
| finance | B3 | 0.034 | 0.020 | 0.002 | 60.44 |
| finance | B4 | 0.480 | 0.353 | 0.000 | 118.56 |

## Challenge/OOD abstention

| Domain | Model | Abstention | Citation-free | Expected behavior |
|---|---:|---:|---:|---:|
| medical | B3 | 1.000 | 1.000 | 1.000 |
| medical | B4 | 1.000 | 1.000 | 1.000 |
| finance | B3 | 1.000 | 1.000 | 1.000 |
| finance | B4 | 1.000 | 1.000 | 1.000 |

## Observed KG effects vs B2 at Recall@5

{"finance": {"helps": 61, "hurts": 19, "neutral": 1067}, "medical": {"helps": 11, "neutral": 51}}
