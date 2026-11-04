"""Serve the notebook-exported RAG+Gemini backend and built React app."""
from pathlib import Path
import argparse,os,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'web/backend'))
from project01_llm_v2.transport import create_app
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8031);parser.add_argument('--live',action='store_true');args=parser.parse_args()
    create_app(P,allow_api=args.live).run(host='127.0.0.1',port=args.port,threaded=True,use_reloader=False,debug=False)
