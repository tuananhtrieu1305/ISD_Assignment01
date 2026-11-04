from pathlib import Path
import sys
root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'TIEU_LUAN_AI_V3_EXECUTION_PLAN.md').exists())
if str(root) not in sys.path: sys.path.insert(0, str(root))
from scripts.demo_phase29 import sample_request, infer
from src.common.contracts import read_json


dataset = 'ch4_gold_pink_sheet'
jobs = {}
for family in ('rnn', 'lstm'):
    request, sample_id = sample_request(dataset, family)
    jobs[family] = infer(request)
    print('TRAIN sample:', sample_id, family)
    for row in jobs[family]['results']:
        print(row['implementation'], row['actual_backend'], row['actual_device'], row['prediction'])
    assert jobs[family]['comparison_valid']
assert jobs['rnn']['input_sha256'] == jobs['lstm']['input_sha256']

for family, phase in (('rnn',28), ('lstm',29)):
    model_id = jobs[family]['results'][0]['model_id']
    contract = read_json(root / f'artifacts/manifests/phase{phase}/runs' / model_id / 'model_contract.json')
    print(family, contract['composition_plain'], 'parameters=',contract['parameter_count'])
    assert sum(layer['kind'] in {'rnn','lstm','dense'} for layer in contract['layers']) == 6

audit = read_json(root / 'artifacts/manifests/phase29/test_verification.json')
print('Saved TEST audit:', audit['status'], audit['test_prediction_rows'])
assert audit['status'] == 'PASS'
assert not any(name in sys.modules for name in ('torch','tensorflow','keras'))
print('No TEST forward or training was executed by this notebook.')