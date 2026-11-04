"""Read-only runtime package audit; no model import, installation or secret output."""
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import sys

PROJECT=Path(__file__).resolve().parents[2]
names=['numpy','scikit-learn','pydantic','langchain-core','langchain-google-genai',
       'langchain-text-splitters','rank-bm25','pyvis','networkx','google-genai','Flask']
versions={}
for name in names:
    try:versions[name]=metadata.version(name)
    except metadata.PackageNotFoundError:versions[name]=None
receipt={'python':sys.version.split()[0],'executable':sys.executable,'packages':versions,
         'gemini_env_present':bool(os.environ.get('GEMINI_API_KEY')),
         'scientific_environment_modified':False,'model_forward':False}
path=PROJECT/'artifacts/llm_v2/phase1/runtime_audit.json'
path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt))
