"""List or resolve per-assignment dataset IDs; no implicit download or training."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"_shared"))
from assignment_runtime import PROJECTS, resolve_dataset
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("project",choices=PROJECTS)
parser.add_argument("dataset_id",nargs="?")
parser.add_argument("--verify",action="store_true")
args=parser.parse_args()
if args.dataset_id:
    value=resolve_dataset(args.project,args.dataset_id,verify=args.verify)
    print(json.dumps(value,ensure_ascii=False,indent=2))
else:
    value=json.loads((ROOT/args.project/"datasets/catalog.json").read_text())
    print(json.dumps([{k:r[k] for k in ("dataset_id","name","status")} for r in value["datasets"]],ensure_ascii=False,indent=2))
