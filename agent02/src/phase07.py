"""AG02 phase7 gate: fifteen memory/time runs, thirty new frozen claims, saved reference reuse."""

import argparse
import json
import os
import xml.etree.ElementTree as ET
from dataclasses import asdict
from pathlib import Path

from .code.augmented import alias_witness, augmented_hash
from .code.augmented_runs import execute_augmented
from .code.baseline_runs import verify_run
from .code.controlled import LearningConfig, MarketConfig
from .code.evaluation.augmented_final import evaluate_augmented
from .code.evaluation.phase07_journal import PREFIX, claim_once, key_for
from .code.training import digest
from .phase01 import preflight
from .phase02 import disk_guard, save_json
from .phase03 import TRAIN_FILES, writer_lock
from .phase04 import verify_lock
from .phase06 import markets, protocol
from .workspace import inside, sha256_file

BASE = Path(__file__).resolve().parent
NEW_FILES = ['phase07.py','code/augmented.py','code/augmented_runs.py','code/market_oracle.py',
    'code/evaluation/augmented_final.py','code/evaluation/phase07_journal.py','tests/test_phase07.py',
    'tests/coverage_phase07.ini','docs/phase07_design.md','scripts/run_agent02_phase07.ps1']
FILES = sorted(set(TRAIN_FILES+NEW_FILES+['phase06.py','code/evaluation/final_v1.py']))


def specs():
    result = [r for r in protocol()['training_runs'] if r['phase']==7]
    if len(result)!=15 or {r['kernel_id'] for r in result}!={'iid','persistent','gold'}:
        raise ValueError('Require15 augmented runs on three kernels')
    return result


def file_rows(paths):
    return [{'path':p,'sha256':sha256_file(inside(BASE,p))} for p in sorted(set(paths))]


def references():
    records=[]
    for phase in (5,6):
        completion = json.loads((BASE/f'artifacts/evaluation/phase{phase:02d}/completion.json').read_text())
        for entry in completion['entries']:
            j=entry['job']
            if phase==5:
                if not ((j['group']=='core' and j['config_id']=='baseline') or
                        (j['group']=='control' and j['kind']=='rule')):
                    continue
                kernel,seed,policy='iid',j['train_seed'],'baseline' if j['group']=='core' else 'rule'
            else:
                if j['group']!='variant' or j['policy_id'] not in ('retrained','rule'):
                    continue
                kernel,seed,policy=j['kernel_id'],j['seed'],'baseline' if j['policy_id']=='retrained' else 'rule'
            result_path=str(Path(entry['complete_path']).with_name('result.json'))
            result=json.loads((BASE/result_path).read_text())
            scenario=j['scenario_spec']
            if (MarketConfig(**scenario['market'])!=markets()[kernel] or result['episodes']!=500 or
                    result['scenario_seed']!=2000000+seed or result['exploration'] is not False):
                raise ValueError('Reference scenarios incompatible')
            records.append({'kernel_id':kernel,'seed':seed,'role':j['role'],'policy_id':policy,'source_phase':phase,
                'source_job':j,'key':entry['key'],'complete_path':entry['complete_path'],'result_path':result_path,
                'result_sha256':sha256_file(BASE/result_path),'complete_sha256':sha256_file(BASE/entry['complete_path']),
                'q_path':j.get('q_path')})
    if len(records)!=60 or len({(r['kernel_id'],r['seed'],r['role'],r['policy_id']) for r in records})!=60:
        raise ValueError('Require60 unique saved reference claims')
    return records


def assert_proof(relative):
    value=json.loads((BASE/relative).read_text())
    for item in value['files']:
        if sha256_file(inside(BASE,item['path']))!=item['sha256']:
            raise ValueError('Phase7 protected input changed:'+item['path'])
    return value


def test_proof():
    xml=ET.parse(BASE/'evidence/phase07/pretrain_tests.xml').getroot()
    if len(xml.findall('.//testcase'))<216 or any(xml.findall('.//'+t) for t in ('failure','error','skipped')):
        raise ValueError('Pretrain tests failed/incomplete')
    if json.loads((BASE/'evidence/phase07/pretrain_coverage.json').read_text())['totals']['percent_covered']<80:
        raise ValueError('Phase7 coverage below80')


def declare():
    runtime=preflight()['runtime']
    test_proof()
    verify_lock(BASE,'evidence/phase06/experiment_lock.json')
    refs=references()
    save_json(BASE,'artifacts/manifests/phase07/reference_index.json',{'status':'SAVED_REFERENCE_ONLY','entries':refs,'forwarded_again':False})
    save_json(BASE,'evidence/phase07/alias_witness.json',alias_witness())
    paths=FILES+['evidence/phase06/experiment_lock.json','data/derived/gold_regime_kernel_v1.json',
        'artifacts/manifests/phase07/reference_index.json','evidence/phase07/alias_witness.json',
        'evidence/phase07/pretrain_tests.xml','evidence/phase07/pretrain_coverage.json']
    paths += [p for r in refs for p in (r['result_path'],r['complete_path'])]+[r['q_path'] for r in refs if r['q_path']]
    value={'schema':'ag02.phase07.train.1','matrix':specs(),'market_configs':{k:asdict(v) for k,v in markets().items()},
        'learning':protocol()['improved_design']['learning_parameters'],'runtime':runtime,'checkpoint_interval':100,
        'new_final_claims':30,'saved_reference_claims':60,'free_bytes':disk_guard(BASE),'files':file_rows(paths),
        'state_order':['demand','own_previous','competitor_previous','remaining_steps'],
        'oracle':'Separate known-model expectation only; no learner labels or sampled final forward'}
    save_json(BASE,'evidence/phase07/train_declaration.json',value)
    return {'status':'DECLARED','runs':15,'q_entries':320,'sha256':sha256_file(BASE/'evidence/phase07/train_declaration.json')}


def update_state(state):
    path=BASE/'evidence/phase07/active_controller.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(state,indent=2)+'\n')
    temp.replace(path)


def train(resume=False):
    declaration=assert_proof('evidence/phase07/train_declaration.json')
    proof=sha256_file(BASE/'evidence/phase07/train_declaration.json')
    state={'stage':'train','status':'RUNNING','pid':os.getpid(),'completed':0,'current':None}
    records=[]
    try:
        for spec in declaration['matrix']:
            state['current']=spec['run_id']
            update_state(state)
            result=execute_augmented(BASE,spec,MarketConfig(**declaration['market_configs'][spec['kernel_id']]),
                LearningConfig(**declaration['learning']),proof,resume=resume,interval=100)
            records.append({'run_id':spec['run_id'],'seed':spec['seed'],'kernel_id':spec['kernel_id'],'status':'TRAINED',
                'q_sha256':result['q_sha256'],'train_wall_seconds':result['train_wall_seconds'],
                'train_cpu_seconds':result['train_cpu_seconds'],'resumed':result['resumed']})
            state['completed']=len(records)
            print(f'{len(records)}/15 TRAIN COMPLETE {spec["run_id"]}',flush=True)
        save_json(BASE,'artifacts/manifests/phase07/train_completion.json',{'status':'COMPLETE','entries':records,'declaration_sha256':proof})
        state.update({'status':'COMPLETE','current':None})
    except BaseException as error:
        state.update({'status':'FAILED_RETAIN_CHECKPOINT','error':str(error)})
        raise
    finally:
        state['pid']=None
        update_state(state)
    return {'status':'COMPLETE','train_runs':15}


def build_jobs():
    train=assert_proof('evidence/phase07/train_declaration.json')
    jobs=[]
    for spec in train['matrix']:
        verify_run(BASE,spec['run_id'])
        qpath=f'artifacts/runs/{spec["run_id"]}/q_table.json'
        q=json.loads((BASE/qpath).read_text())
        for role in (0,1):
            scenario={'market':train['market_configs'][spec['kernel_id']],'episodes':500,'scenario_seed':2000000+spec['seed'],
                'rng':protocol()['rng'],'initial_history':[0,0],'tape_engine':'original_Tape.generate_v1'}
            jobs.append({'job_id':f'augmented/{spec["kernel_id"]}/s{spec["seed"]:04d}/role{role}',
                'study_id':'ag02_phase07_augmented_v1','kernel_id':spec['kernel_id'],'seed':spec['seed'],'role':role,
                'policy_id':'augmented','policy_sha256':augmented_hash(q),'scenario_sha256':digest(scenario),
                'scenario_spec':scenario,'q_path':qpath,'q_file_sha256':sha256_file(BASE/qpath)})
    if len(jobs)!=30 or len({key_for(j) for j in jobs})!=30:
        raise ValueError('Require30 distinct augmented final claims')
    return jobs


def declare_eval():
    test_proof()
    jobs=build_jobs()
    paths=FILES+['evidence/phase07/train_declaration.json','artifacts/manifests/phase07/train_completion.json']+[j['q_path'] for j in jobs]
    value={'schema':'ag02.phase07.final.1','jobs':jobs,'new_claims':30,'saved_reference_claims':60,
        'expected_new_episode_rows':15000,'expected_new_market_steps':300000,'files':file_rows(paths),'free_bytes':disk_guard(BASE)}
    save_json(BASE,'evidence/phase07/eval_declaration.json',value)
    return {'status':'DECLARED','claims':30,'sha256':sha256_file(BASE/'evidence/phase07/eval_declaration.json')}


def forward(job):
    path=BASE/job['q_path']
    if sha256_file(path)!=job['q_file_sha256']:
        raise ValueError('Augmented Q input changed')
    q=json.loads(path.read_text())
    if augmented_hash(q)!=job['policy_sha256']:
        raise ValueError('Augmented Q payload changed')
    scenario=job['scenario_spec']
    result=evaluate_augmented(q,MarketConfig(**scenario['market']),episodes=500,scenario_seed=scenario['scenario_seed'],
        role=job['role'],guard=lambda:disk_guard(BASE))
    if sha256_file(path)!=job['q_file_sha256']:
        raise RuntimeError('Source augmented Q changed during final')
    return {**result,'partition':'phase07_frozen_final','job_id':job['job_id']}


def evaluate():
    declaration=assert_proof('evidence/phase07/eval_declaration.json')
    proof=sha256_file(BASE/'evidence/phase07/eval_declaration.json')
    state={'stage':'evaluate','status':'RUNNING','pid':os.getpid(),'completed':0,'current':None}
    records=[]
    try:
        for job in declaration['jobs']:
            state['current']=job['job_id']
            update_state(state)
            disk_guard(BASE)
            saved=claim_once(BASE,job,proof,lambda job=job:forward(job))
            records.append({'job':job,'key':saved['key'],'complete_path':PREFIX+'/'+saved['key']+'/complete.json'})
            state['completed']=len(records)
            print(f'{len(records)}/30 EVALUATED {job["job_id"]}',flush=True)
        save_json(BASE,'artifacts/evaluation/phase07/completion.json',{'status':'EVALUATED','entries':records,'unique_claims':30,'declaration_sha256':proof})
        state.update({'status':'COMPLETE','current':None})
    except BaseException as error:
        state.update({'status':'FAILED_RETAIN_CLAIMS','error':str(error)})
        raise
    finally:
        state['pid']=None
        update_state(state)
    return {'status':'COMPLETE','new_claims':30}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task',choices=('status','declare','train','declare-eval','evaluate'))
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.task=='status':
        path=BASE/'evidence/phase07/active_controller.json'
        result={'phase':7,'controller':json.loads(path.read_text()) if path.exists() else None,
            'completed_train_runs':sum((BASE/'artifacts/runs'/s['run_id']/'complete.json').exists() for s in specs())}
    else:
        with writer_lock(BASE):
            result={'declare':declare,'train':lambda:train(args.resume),'declare-eval':declare_eval,'evaluate':evaluate}[args.task]()
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=='__main__':
    main()
