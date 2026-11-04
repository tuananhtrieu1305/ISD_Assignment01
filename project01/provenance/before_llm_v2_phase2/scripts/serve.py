"""Serve the built React app and notebook-exported API in one local process."""
from pathlib import Path
import argparse
import os
import sys
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'web/backend'))
from project01_core.transport import create_app
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8031);args=parser.parse_args()
    create_app(PROJECT).run(host='127.0.0.1',port=args.port,debug=False,threaded=False,use_reloader=False)
