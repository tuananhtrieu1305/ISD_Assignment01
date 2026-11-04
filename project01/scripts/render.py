"""Render entry point: prebuilt medical package + source parity, no historical data dependency."""
from pathlib import Path
import argparse
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
PROJECT=ROOT/'project01'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['build','start','check']);args=parser.parse_args()
    if args.stage=='build':
        subprocess.run([sys.executable,'-m','pip','install','-r',str(PROJECT/'web/backend/requirements.txt')],check=True)
    if args.stage in {'check','build'}:
        subprocess.run([sys.executable,'-B',str(PROJECT/'scripts/notebook_source.py'),'check'],check=True)
        sys.path.insert(0,str(PROJECT/'web/backend'))
        from project01_core.foundation import Runtime
        runtime=Runtime(PROJECT/'artifacts/package/v1')
        print('Render source/package check PASS',len(runtime.chunks));return
    for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
    os.execvp('gunicorn',['gunicorn','--chdir',str(PROJECT/'web/backend'),'app:app','--bind','0.0.0.0:'+os.environ.get('PORT','10000'),'--workers','1','--threads','1','--timeout','40','--access-logfile','-'])

if __name__=='__main__':main()
