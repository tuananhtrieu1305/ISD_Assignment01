# Phase 14 build report

- Locked config SHA-256: `ea5b3546a8e408648f5024d62bd0cb3584784ead2f594e126d2dea356240653d`.
- B2 selected sparse weight on validation: `0.75`.
- TEST status: `SEALED_NOT_RUN`.
- All models use the same per-domain corpus, validation queries, top-k and grounded answer contract.
- Program accuracy is not applicable to the extractive B0-B2 answer layer; FinQA execution accuracy is reported as normalized numeric/string exact match.

## Validation summary

| Domain | Model | Chunk R@5 | MRR@10 | Token F1 | Abstain | p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| medical | B0 | 0.333 | 0.255 | 0.207 | 0.000 | 0.28 |
| medical | B1 | 0.394 | 0.266 | 0.217 | 0.000 | 1.30 |
| medical | B2 | 0.364 | 0.261 | 0.208 | 0.000 | 1.69 |
| finance | B0 | 0.535 | 0.423 | 0.000 | 0.007 | 38.12 |
| finance | B1 | 0.245 | 0.173 | 0.000 | 0.092 | 48.92 |
| finance | B2 | 0.450 | 0.326 | 0.000 | 0.008 | 87.09 |
