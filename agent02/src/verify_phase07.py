"""Audit saved Phase7 runs/claims/references and analytic tables; never train or sampled-forward."""

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

from .code.augmented import SHAPE, alias_witness, augmented_hash, state_index
from .code.evaluation.aggregate_v1 import validate_result
from .code.evaluation.phase07_journal import PREFIX, key_for, read_claim
from .code.phase07_analysis import aggregate
from .code.training import digest
from .phase01 import preflight
from .phase02 import save_json
from .phase03 import writer_lock
from .phase07 import assert_proof
from .phase07_reporting import collect, supporting_tables
from .verify_phase06 import check_table
from .workspace import sha256_file

BASE=Path(__file__).resolve().parent


def audit():
    parent=preflight()
    train=assert_proof('evidence/phase07/train_declaration.json')
    evaluation=assert_proof('evidence/phase07/eval_declaration.json')
    old={}
    for relative in ('phase01/input_lock.json','phase02/protocol_lock.json','phase03/experiment_lock.json',
                     'phase04/experiment_lock.json','phase05/experiment_lock.json','phase06/experiment_lock.json'):
        for item in json.loads((BASE/'evidence'/relative).read_text())['files']:
            if item['path'] in old and old[item['path']]!=item['sha256']:
                raise ValueError('Old hashes disagree')
            old[item['path']]=item['sha256']
    for relative,fingerprint in old.items():
        if sha256_file(BASE/relative)!=fingerprint:
            raise ValueError('Old protected file changed:'+relative)
    if json.loads((BASE/'evidence/phase07/alias_witness.json').read_text())!=alias_witness():
        raise ValueError('Analytic alias witness differs')
    controller=json.loads((BASE/'evidence/phase07/active_controller.json').read_text())
    if controller['status']!='COMPLETE' or controller['stage']!='evaluate' or controller['pid'] is not None:
        raise ValueError('Controller unfinished')
    completed=json.loads((BASE/'artifacts/manifests/phase07/train_completion.json').read_text())
    if len(completed['entries'])!=15 or completed['declaration_sha256']!=sha256_file(BASE/'evidence/phase07/train_declaration.json'):
        raise ValueError('Train index differs')
    registry=[]
    for spec in train['matrix']:
        folder=BASE/'artifacts/runs'/spec['run_id']
        result=json.loads((folder/'complete.json').read_text())
        for item in result['files']:
            path=BASE/item['path']
            if sha256_file(path)!=item['sha256'] or path.stat().st_size!=item['bytes']:
                raise ValueError('Augmented train artifact changed')
        saved=json.loads((folder/'checkpoint_e005000.json').read_text())
        body={k:v for k,v in saved.items() if k!='sha256'}
        if digest(body)!=saved['sha256'] or saved['completed']!=5000 or len(saved['rows'])!=5000:
            raise ValueError('Final train checkpoint differs')
        if len(list(folder.glob('checkpoint_e*.json')))!=51 or np.array(json.loads((folder/'checkpoint_e000000.json').read_text())['q']).any():
            raise ValueError('Checkpoint cadence/zero init differs')
        q=json.loads((folder/'q_table.json').read_text())
        if q!=saved['q'] or augmented_hash(q)!=result['q_sha256']:
            raise ValueError('Train Q hash differs')
        visits=np.array(saved['visits'])
        if (visits.shape!=SHAPE or visits.sum()!=100000 or (visits<0).any() or
                not (visits.sum(axis=(0,1,2,4))==5000).all()):
            raise ValueError('Train visits/time counts differ')
        check_table(folder/'episode_rewards.csv',saved['rows'])
        if any(r['episode']!=i+1 or np.array(r['action_counts']).sum(axis=1).tolist()!=[20,20] for i,r in enumerate(saved['rows'])):
            raise ValueError('Train row/action counts differ')
        policies=json.loads((folder/'policy.json').read_text())
        if len(policies)!=160 or len({tuple(p['state']) for p in policies})!=160:
            raise ValueError('Require160 unique full-state policy rows')
        for policy in policies:
            index=state_index(policy['state'])
            values=np.array(q)[index]
            if (policy['q_values']!=values.tolist() or policy['visits']!=visits[index].tolist() or
                policy['greedy_actions']!=np.flatnonzero(np.isclose(values,values.max())).tolist()):
                raise ValueError('Full-state policy differs')
        registry.append({'run_id':spec['run_id'],'kernel_id':spec['kernel_id'],'seed':spec['seed'],'status':'TRAINED_EVALUATED',
            'q_path':(folder/'q_table.json').relative_to(BASE).as_posix(),'q_sha256':result['q_sha256'],
            'q_file_sha256':sha256_file(folder/'q_table.json'),'q_entries':320})
    final=json.loads((BASE/'artifacts/evaluation/phase07/completion.json').read_text())
    proof=sha256_file(BASE/'evidence/phase07/eval_declaration.json')
    if final['declaration_sha256']!=proof or len(final['entries'])!=30 or len(evaluation['jobs'])!=30:
        raise ValueError('New evaluation counts differ')
    if len(list((BASE/PREFIX).iterdir()))!=30 or list((BASE/PREFIX).rglob('failure.json')):
        raise ValueError('Unexpected/missing/failed Phase7 claim')
    for entry,job in zip(final['entries'],evaluation['jobs'],strict=True):
        if entry['job']!=job or entry['key']!=key_for(job):
            raise ValueError('Final job/key differs')
        read_claim(BASE,job,proof)
        folder=BASE/PREFIX/entry['key']
        claim=json.loads((folder/'claim.json').read_text())
        value=json.loads((folder/'result.json').read_text())
        validate_result(value)
        if claim['job']!=job or claim['proof_sha256']!=proof:
            raise ValueError('Claim registration differs')
        if (value['episodes']!=500 or value['steps']!=10000 or value['exploration'] is not False or
            value['job_id']!=job['job_id'] or value['role']!=job['role'] or value['scenario_seed']!=2000000+job['seed'] or
            value['policy_sha256']!=job['policy_sha256'] or value['q_hash_before']!=job['policy_sha256'] or
            value['q_hash_after']!=value['q_hash_before'] or digest(job['scenario_spec'])!=job['scenario_sha256'] or
            value['partition']!='phase07_frozen_final'):
            raise ValueError('Final policy/budget/scenario differs')
        with (folder/'episodes.csv').open() as stream:
            rows=[{k:json.loads(v) for k,v in row.items()} for row in csv.DictReader(stream)]
        visits=np.array([r['state_visits'] for r in rows])
        if (rows!=value['rows'] or [r['episode'] for r in rows]!=list(range(1,501)) or visits.shape!=(500,160) or
            (visits<0).any() or not (visits.sum(axis=1)==20).all() or visits.sum(axis=0).tolist()!=value['state_visits'] or
            not (visits.reshape(500,2,2,2,20).sum(axis=(1,2,3))==1).all()):
            raise ValueError('Raw final rows/visits/time count differs')
    refs=json.loads((BASE/'artifacts/manifests/phase07/reference_index.json').read_text())['entries']
    if len(refs)!=60 or len({(r['kernel_id'],r['policy_id'],r['seed'],r['role']) for r in refs})!=60:
        raise ValueError('Reference count differs')
    for reference in refs:
        saved=json.loads((BASE/reference['complete_path']).read_text())
        if (saved['evaluation_count']!=1 or sha256_file(BASE/reference['complete_path'])!=reference['complete_sha256'] or
                sha256_file(BASE/reference['result_path'])!=reference['result_sha256']):
            raise ValueError('Reference receipt/result differs')
        j=reference['source_job']
        value=json.loads((BASE/reference['result_path']).read_text())
        validate_result(value)
        if (j['scenario_spec']['market']!=train['market_configs'][reference['kernel_id']] or value['episodes']!=500 or
            value['scenario_seed']!=2000000+reference['seed'] or value['role']!=reference['role'] or value['exploration'] is not False):
            raise ValueError('Saved reference scenarios incompatible')
    data=aggregate(collect())
    support=supporting_tables(train)
    for name,values in {**data,**support}.items():
        check_table(BASE/'artifacts/metrics/phase07'/(name+'.csv'),values)
    if len(support['model_expectations'])!=45 or len(support['oracle_summary'])!=3:
        raise ValueError('Analytic table size differs')
    manifest=json.loads((BASE/'artifacts/figures/phase07/manifest.json').read_text())
    for item in manifest['files']:
        if sha256_file(BASE/item['path'])!=item['sha256']:
            raise ValueError('Report/figure/table hash changed')
    if sha256_file(BASE/'phase07_reporting.py')!=manifest['generator_sha256']:
        raise ValueError('Report generator changed')
    qa=json.loads((BASE/'evidence/phase07/visual_qa.json').read_text())
    if qa['status']!='PASS' or len(qa['images'])!=4:
        raise ValueError('Require actual four-image visual QA')
    for item in qa['images']:
        if not item['inspected'] or sha256_file(BASE/item['path'])!=item['sha256']:
            raise ValueError('Visual QA hash changed')
        pixels=np.array(Image.open(BASE/item['path']).convert('RGB'))
        if not np.array_equal(pixels[...,0],pixels[...,1]) or not np.array_equal(pixels[...,1],pixels[...,2]):
            raise ValueError('Image is not grayscale')
    tests=ET.parse(BASE/'evidence/phase07/final_tests.xml').getroot()
    count=len(tests.findall('.//testcase'))
    coverage=json.loads((BASE/'evidence/phase07/final_coverage.json').read_text())['totals']
    quality=json.loads((BASE/'evidence/phase07/quality_checks.json').read_text())
    if count<221 or any(tests.findall('.//'+t) for t in ('failure','error','skipped')) or coverage['percent_covered']<80:
        raise ValueError('Test/coverage failed')
    if quality['status']!='PASS' or any(quality['exit_codes'].values()):
        raise ValueError('Quality checks failed')
    all_specs=json.loads((BASE/'docs/protocol_v1.json').read_text())['training_runs']
    if len(all_specs)!=56 or sum(s['learners'] for s in all_specs)!=61:
        raise ValueError('Registered scientific budget differs')
    for spec in all_specs:
        done=json.loads((BASE/'artifacts/runs'/spec['run_id']/'complete.json').read_text())
        if done['status']!='COMPLETE':
            raise ValueError('A registered scientific run remains unfinished')
    receipt={'status':'PASS','phase':7,'train_market_runs':15,'train_episodes':75000,'train_market_steps':1500000,
        'augmented_learner_instances':15,'q_values_per_learner':320,'new_final_claims':30,'evaluation_count_each':1,
        'new_final_episode_rows':15000,'new_final_market_steps':300000,'saved_reference_claims_reused':60,'reference_forwards_added':0,
        'combined_comparison_members':90,'combined_saved_episode_rows':45000,'combined_saved_market_steps':900000,
        'registered_market_runs_total_completed':56,'registered_learner_instances_total_completed':61,
        'prior_protected_files_preserved':len(old),'selected_parent_assets_preserved':len(parent['preservation']),
        'oracle_scope':'Known simulator/fixed rule analytic expectation recomputed without sampled forward or training labels',
        'tables_csv':8,'figures_explained_and_viewed':4,'tests_passed':count,'skipped':0,
        'coverage_combined_percent':coverage['percent_covered'],
        'coverage_scope':'augmented,augmented_runs,augmented_final,phase07_journal,market_oracle,phase07_analysis only; excludes CLI/plots/auditor/frozen baseline',
        'next_phase':8}
    return registry,receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal',action='store_true')
    args=parser.parse_args()
    with writer_lock(BASE):
        entries,receipt=audit()
        registry={'phase':7,'status':'TRAINED_EVALUATED','entries':entries,'new_final_completion':'artifacts/evaluation/phase07/completion.json',
                  'saved_reference_index':'artifacts/manifests/phase07/reference_index.json'}
        target='artifacts/manifests/phase07/trained_evaluated_registry.json'
        if args.seal:
            save_json(BASE,target,registry)
        elif json.loads((BASE/target).read_text())!=registry:
            raise ValueError('Registry differs')
        paths=[BASE/p for p in ['phase07.py','phase07_reporting.py','verify_phase07.py','code/augmented.py','code/augmented_runs.py',
            'code/evaluation/augmented_final.py','code/evaluation/phase07_journal.py','code/market_oracle.py','code/phase07_analysis.py',
            'tests/test_phase07.py','tests/test_phase07_analysis.py','tests/coverage_phase07.ini','tests/coverage_phase07_final.ini',
            'docs/phase07_design.md','docs/phase07_report.md','docs/phase07_operations.md','scripts/run_agent02_phase07.ps1',
            'report/sections/phase07_improved_agent.md','evidence/phase06/experiment_lock.json']]
        for folder in ('evidence/phase07','artifacts/manifests/phase07','artifacts/evaluation/phase07','artifacts/metrics/phase07','artifacts/figures/phase07'):
            paths += [p for p in (BASE/folder).rglob('*') if p.is_file() and p.name not in
                      ('.coverage','.coverage_final','experiment_lock.json','verification.json','active_controller.json')]
        for spec in json.loads((BASE/'evidence/phase07/train_declaration.json').read_text())['matrix']:
            paths += [p for p in (BASE/'artifacts/runs'/spec['run_id']).rglob('*') if p.is_file()]
        lock={'schema':'ag02.phase07.release.1','files':[{'path':p.relative_to(BASE).as_posix(),'bytes':p.stat().st_size,
            'sha256':sha256_file(p)} for p in sorted(set(paths))]}
        if args.seal:
            save_json(BASE,'evidence/phase07/experiment_lock.json',lock)
        elif json.loads((BASE/'evidence/phase07/experiment_lock.json').read_text())!=lock:
            raise ValueError('Release differs')
        receipt.update({'locked_files':len(lock['files']),'experiment_lock_sha256':sha256_file(BASE/'evidence/phase07/experiment_lock.json')})
        if args.seal:
            save_json(BASE,'evidence/phase07/verification.json',receipt)
        elif json.loads((BASE/'evidence/phase07/verification.json').read_text())!=receipt:
            raise ValueError('Verification differs')
        print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
