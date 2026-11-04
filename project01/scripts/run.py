"""Standalone project runner; reuse pinned runtime without modifying 11 old projects."""
from pathlib import Path
import argparse
import json
import os
import runpy
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
PROJECT=ROOT/'project01'

def activate():
    if sys.platform!='linux' or '.venv-torch' not in sys.executable or sys.version_info[:2]!=(3,11):
        raise RuntimeError('Use the existing WSL Ubuntu .venv-torch Python 3.11 kernel')
    os.environ['CUDA_VISIBLE_DEVICES']='-1'
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
    sys.path.insert(0,str(PROJECT/'web/backend'))
    os.environ['PROJECT01_ROOT']=str(PROJECT)
    os.environ['MPLCONFIGDIR']=str(PROJECT/'artifacts/plot_style')
    os.chdir(PROJECT)
    return {'project':'project01','canonical_root':str(PROJECT),'cwd':str(PROJECT),'framework':'numpy_cpu','python':sys.executable,'output':str(PROJECT/'artifacts'),'gpu_training':False,'old_runtime_view_required':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect',action='store_true')
    parser.add_argument('--probe',action='store_true')
    parser.add_argument('--notebook')
    parser.add_argument('--script')
    args=parser.parse_args()
    context=activate()
    if args.script:
        path=(PROJECT/args.script).resolve()
        if not path.is_relative_to(PROJECT) or not path.is_file():raise ValueError('Script outside project01')
        sys.argv=[str(path)];runpy.run_path(str(path),run_name='__main__');return
    notebook='01_Data_KB_RAG.ipynb' if args.probe else args.notebook
    if not notebook:
        print(json.dumps(context,ensure_ascii=False,indent=2));return
    name=Path(notebook).name
    config=json.loads((PROJECT/'project.json').read_text())
    if name not in [Path(x['path']).name for x in config['notebooks']]:raise ValueError('Unknown notebook')
    if name!='01_Data_KB_RAG.ipynb' and config['phase']==1:
        raise ValueError('Phase 1 only executes the foundation probe; other notebooks await Phase 2')
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager
    document=nbformat.read(PROJECT/'notebooks'/name,as_version=4)
    manager=KernelManager()
    manager.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
    client=NotebookClient(document,timeout=180,km=manager,resources={'metadata':{'path':str(PROJECT)}})
    client.execute(cleanup_kc=True)
    output=PROJECT/'artifacts/notebook_runs'/(Path(name).stem+'-'+str(time.time_ns())+'.ipynb')
    output.parent.mkdir(parents=True,exist_ok=True);nbformat.write(document,output)
    print(str(output))

if __name__=='__main__':main()
