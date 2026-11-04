"""Current materializer: Phase2 frozen recipe plus Phase3 source-location overlay."""
from pathlib import Path
import argparse
import json
from materialize_project import materialize
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project',required=True,choices=['A01','A02','A03','A04','A05','A06','tieuluan1','tieuluan2','tieuluan3','agent01','agent02'])
parser.add_argument('--copy-only',action='store_true')
args=parser.parse_args()
recipe=json.loads((ROOT/'docs/reorganization/phase2/runtime_view_map.json').read_text())
overlay=json.loads((ROOT/'docs/reorganization/phase3/runtime_source_overlay.json').read_text())
index={r['target']:r for r in overlay['files']}
rows=[]
for original in recipe['files']:
    if original['project']!=args.project:continue
    row=dict(original)
    if row['target'] in index:row['source']=index[row['target']]['source']
    rows.append(row)
print({'project':args.project,'created':materialize(ROOT,rows,copy_only=args.copy_only),'source_overlay':'Phase3','symlinks_required':False})
