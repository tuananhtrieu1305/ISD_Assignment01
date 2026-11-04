# Phase 20 cleanup policy

This policy records the destructive scope authorized by `làm phase 20`. The file-level
inventory in `artifacts/manifests/phase20/before-files.csv` is the recovery index.
The final retained form is `before-files.csv.gz`; per-file results are in `file-outcomes.csv.gz`.

## Preserve

- V2 release DOCX files and the A05/A06 reference DOCX files, moved to `releases/v2/`.
- Source code, notebooks, tests, report source, bibliography, configuration, and plans.
- Ch5 raw MedQuAD/FinQA/Wikidata snapshot, source revision metadata, locked metrics,
  manifests, Phase 15 public TEST predictions, and compact deployment artifacts.
- Current React web and Python backend source until their Phase 32/33 migration.

## Remove or regenerate

- Virtual environments, `node_modules`, build output, Python/Jupyter/test caches.
- The legacy mobile client, because V3 targets React web and Python API only.
- Old A05/A06/pipeline/pipeline04 datasets, model checkpoints, experiment output, and
  report renders that are recoverable from Git or superseded by V3 datasets.
- Root legacy datasets/artifacts and V2 Ch2-Ch4 experiment artifacts that Phase 23–29 replace.
- Ch5 processed graph/index data and Phase 14 predictions that can be regenerated without
  rerunning the sealed Phase 15 public TEST.
- DOCX page-render QA directories after the release files are hashed and preserved.

## Safety constraints

- Every deletion target is resolved to an absolute path and must remain under
  `C:\DATA\assign`.
- `.git` and Git history are never modified by the cleanup.
- Tracked deletions remain recoverable from Git. Untracked Ch5 public TEST evidence is kept.
- No wildcard or unresolved environment variable is used as a destructive target.
- Immutable raw Ch5 content is excluded from cache cleanup, including cache files already present upstream.

