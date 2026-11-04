"""Compatibility namespace for V2 code and serialized KG-RAG class identities.

The implementation lives in src/term_paper. Keep this namespace until the old
joblib artifacts have been migrated and verified in Phase 30.
"""

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parents[1] / "src" / "term_paper")]
