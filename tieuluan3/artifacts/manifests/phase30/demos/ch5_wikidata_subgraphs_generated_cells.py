from pathlib import Path
import sys
root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'TIEU_LUAN_AI_V3_EXECUTION_PLAN.md').exists())
if str(root) not in sys.path: sys.path.insert(0, str(root))
from src.ch05_knowledge_rag.structural import inspect_entity
from src.common.contracts import read_json
index = read_json(root / 'data/raw/ch5/wikidata/snapshot_index.json')
result = [inspect_entity(r['qid']) for r in index['entities']]
for row in result: print(row['qid'], row['revision_id'], row['claim_count'], row['citation']['source_sha256'])
assert len(result) == 10 and sum(r['claim_count'] for r in result) == 2056
assert all(not r['qa_benchmark'] for r in result)
assert not any(name in sys.modules for name in ('torch','tensorflow','keras'))
print('No TEST evaluation, fit, download or external API call executed.')
