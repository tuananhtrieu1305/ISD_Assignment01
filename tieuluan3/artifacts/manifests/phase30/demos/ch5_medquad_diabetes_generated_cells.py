from pathlib import Path
import sys
root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'TIEU_LUAN_AI_V3_EXECUTION_PLAN.md').exists())
if str(root) not in sys.path: sys.path.insert(0, str(root))
from src.ch05_knowledge_rag.service import KgRagService, sample_request
service = globals().get('phase30_service') or KgRagService()
request = sample_request('ch5_medquad_diabetes')
result = service.compare(request)
assert result['job']['status'] == 'succeeded'
assert result['job']['comparison_valid']
assert len(result['job']['results']) == 5
for row in result['job']['results']:
    print(row['implementation'], row['actual_backend'], row['actual_device'], row['prediction']['abstained'], row['prediction']['text'], row['prediction']['citations'])
assert not result['public_test_evaluation_executed']
assert not any(name in sys.modules for name in ('torch','tensorflow','keras'))
print('No TEST evaluation, fit, download or external API call executed.')
