"""Explicit stages; evaluation is never triggered by Run All or the web UI."""
from pathlib import Path
import argparse
import os
import sys
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'web/backend'))
from project01_core.evaluation import run_cases

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['development','evaluation']);parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    print(run_cases(PROJECT,args.stage,resume=args.resume))
