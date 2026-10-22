# Phase 13 build report

- Extractor: `phase13-deterministic-v1`
- TEST policy: `SEALED_NOT_USED_FOR_TUNING`
- Medical: 1,336 nodes, 1,506 edges, link coverage 0.048.
- Finance: 99,355 nodes, 97,809 edges, link coverage 0.035.
- Entity-link audit: 203 rows; 8 linked; 195 unresolved; 0 forced ambiguous links.
- Both graph schemas: PASS; provenance coverage: 100% nodes and edges; duplicate rates: 0.
- Offline exports: JSONL + GraphML + bidirectional adjacency JSON.
