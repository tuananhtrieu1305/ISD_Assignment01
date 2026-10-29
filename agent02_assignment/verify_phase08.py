"""Read-only content/provenance audit and Phase8 seal. Never runs scientific models."""

import argparse
import csv
import fcntl
import json
import math
import re
import statistics
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path

from .code.report_assets import extract_code, readable_prose, render_tokens, validate_structure
from .compile_phase08 import assets
from .phase01 import preflight
from .workspace import sha256_file

BASE=Path(__file__).resolve().parent
OUT=BASE/'report/phase08'


def load(path):
    return json.loads((BASE/path).read_text(encoding='utf-8'))


def csv_rows(path):
    with (BASE/path).open(encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def save(path,value):
    target=BASE/path
    if target.exists():
        if json.loads(target.read_text())!=value:
            raise ValueError('Keep previous evidence; write a revision:'+path)
        return
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def calculations():
    checks=[]
    def equal(name,actual,expected):
        if not math.isclose(float(actual),float(expected),rel_tol=0,abs_tol=1e-12):
            raise ValueError('Saved arithmetic/statistics differs:'+name)
        checks.append({'name':name,'actual':float(actual),'expected':float(expected),'status':'PASS'})
    qnew=Decimal(4)+Decimal('.1')*(Decimal(6)+Decimal('.9')*Decimal(5)-Decimal(4))
    equal('Q3 hypothetical Q update',qnew,4.65)
    equal('Q5 no_discount margin',Decimal(10)-Decimal(5),5)
    equal('Q5 discount margin',Decimal(10)*Decimal('.8')-Decimal(5),3)
    for row in csv_rows('artifacts/metrics/phase03_train_summary.csv'):
        run='ref/baseline/s0042' if row['track']=='REF' else 'controlled/iid/baseline/s0011'
        raw=csv_rows('artifacts/runs/'+run+'/episode_rewards.csv')
        if len(raw)!=5000:
            raise ValueError('Baseline raw count differs')
        for agent in ('rl','rule'):
            total=sum(float(r[agent+'_episode_reward']) for r in raw)
            equal(run+'/'+agent+'/last_cumulative_reward',total,row[agent+'_total_reward'])
            equal(run+'/'+agent+'/mean',total/100000,row[agent+'_mean_reward_per_step'])
    seed4=csv_rows('artifacts/metrics/phase04/seed_train_summary.csv')
    for row in csv_rows('artifacts/metrics/phase04/config_train_summary.csv'):
        values=[float(r['rl_mean_reward_per_step']) for r in seed4 if r['config_id']==row['config_id']]
        equal('train/'+row['config_id']+'/mean',statistics.mean(values),row['rl_train_mean'])
        equal('train/'+row['config_id']+'/std',statistics.stdev(values),row['rl_train_std'])
    seed5=csv_rows('artifacts/metrics/phase05/multi_seed.csv')
    for row in load('artifacts/metrics/phase05/config_summary.json'):
        values=[float(r['target_mean']) for r in seed5 if r['config_id']==row['config_id']]
        equal('final/'+row['config_id']+'/mean',statistics.mean(values),row['target_mean'])
        equal('final/'+row['config_id']+'/std',statistics.stdev(values),row['target_std'])
    for row in csv_rows('artifacts/metrics/phase05/baseline_reward.csv'):
        equal('Q6/'+row['track']+row['train_seed']+'/Qmean',float(row['target_total'])/float(row['steps']),row['target_mean'])
        equal('Q6/'+row['track']+row['train_seed']+'/rulemean',float(row['opponent_total'])/float(row['steps']),row['opponent_mean'])
    seed6=csv_rows('artifacts/metrics/phase06/q8_pair.csv')
    for row in csv_rows('artifacts/metrics/phase06/q8_summary.csv'):
        values=[float(r['target_mean']) for r in seed6 if r['checkpoint_episode']==row['checkpoint_episode']]
        equal('q8/'+row['checkpoint_episode']+'/mean',statistics.mean(values),row['target_mean'])
        equal('q8/'+row['checkpoint_episode']+'/std',statistics.stdev(values),row['target_std'])
    variant=csv_rows('artifacts/metrics/phase06/variant_seed.csv')
    for row in csv_rows('artifacts/metrics/phase06/variant_summary.csv'):
        values=[float(r['target_mean']) for r in variant if r['kernel']==row['kernel'] and r['policy']==row['policy']]
        equal('variant/'+row['kernel']+'/'+row['policy']+'/mean',statistics.mean(values),row['target_mean'])
        equal('variant/'+row['kernel']+'/'+row['policy']+'/std',statistics.stdev(values),row['target_std'])
    gold=load('data/derived/gold_regime_kernel_v1.json')
    for i in (0,1):
        for j in (0,1):
            counts=gold['transition_counts'][i]
            equal(f'GoldLaplace/{i}/{j}',(counts[j]+1)/(sum(counts)+2),gold['kernel'][i][j])
    seed7=csv_rows('artifacts/metrics/phase07/seed_comparison.csv')
    for row in csv_rows('artifacts/metrics/phase07/policy_summary.csv'):
        values=[float(r['target_mean']) for r in seed7 if r['kernel']==row['kernel'] and r['policy']==row['policy']]
        equal('improved/'+row['kernel']+'/'+row['policy']+'/mean',statistics.mean(values),row['profit_mean'])
        equal('improved/'+row['kernel']+'/'+row['policy']+'/std',statistics.stdev(values),row['profit_std'])
    delta=csv_rows('artifacts/metrics/phase07/paired_deltas.csv')
    for row in csv_rows('artifacts/metrics/phase07/delta_summary.csv'):
        for field in ('delta_vs_baseline','delta_vs_rule'):
            values=[float(r[field]) for r in delta if r['kernel']==row['kernel']]
            equal('paired/'+row['kernel']+'/'+field+'/mean',statistics.mean(values),row[field+'_mean'])
            equal('paired/'+row['kernel']+'/'+field+'/std',statistics.stdev(values),row[field+'_std'])
    return {'status':'PASS','checks':checks,'scope':'saved raw reward/cumulative totals,seed-level means/std and required hypothetical calculations; no scientific forward'}


def audit():
    parent=preflight()
    old={}
    for relative in ('phase01/input_lock.json','phase02/protocol_lock.json',*[f'phase{p:02d}/experiment_lock.json' for p in range(3,8)]):
        for item in load('evidence/'+relative)['files']:
            if item['path'] in old and old[item['path']]!=item['sha256']:
                raise ValueError('Conflicting prior file hashes')
            old[item['path']]=item['sha256']
    for relative,fingerprint in old.items():
        if sha256_file(BASE/relative)!=fingerprint:
            raise ValueError('Prior protected file changed:'+relative)
    book=assets()
    text=(OUT/'manuscript.md').read_text(encoding='utf-8')
    expected,used=render_tokens(readable_prose((OUT/'source_template.md').read_text(encoding='utf-8')),book['tokens'])
    if text!=readable_prose(expected):
        raise ValueError('Manuscript differs from source-bound assembly')
    structure=validate_structure(text)
    if load('report/phase08/numeric_claims.json')!=book['numbers'] or load('report/phase08/tables.json')!=book['tables']:
        raise ValueError('Numeric/table receipt differs')
    index=load('report/phase08/input_index.json')
    for item in index:
        if sha256_file(BASE/item['path'])!=item['sha256'] or (BASE/item['path']).stat().st_size!=item['bytes']:
            raise ValueError('Report input changed:'+item['path'])
        if item['path'] in old and old[item['path']]!=item['sha256']:
            raise ValueError('Report input differs from scientific lock')
    snippets=re.findall(r'```python\n([\s\S]*?)\n```',text)
    excerpts=load('report/phase08/code_excerpt_index.json')
    if excerpts!=book['excerpts'] or snippets!=[e['text'] for e in excerpts]:
        raise ValueError('Code excerpt changed from exact source')
    if 'if terminal' not in next(e['text'] for e in excerpts if e['id']=='E03'):
        raise ValueError('Essential terminal update omitted')
    figures=load('report/phase08/figure_catalog.json')
    if len(figures)!=20:
        raise ValueError('Require twenty figures')
    reviewed=load('evidence/phase08/content_review.json')
    if reviewed['status']!='PASS' or reviewed['manuscript_sha256']!=sha256_file(OUT/'manuscript.md'):
        raise ValueError('Human content review required for this manuscript')
    for figure in figures:
        if len(figure['caption_text'])<180 or sha256_file(BASE/figure['path'])!=figure['sha256']:
            raise ValueError('Figure or explanation missing')
        prior=load(f'evidence/phase{figure["phase"]:02d}/visual_qa.json')
        entry=next(r for r in prior['images'] if r['path']==figure['path'])
        if prior['status']!='PASS' or not entry['inspected'] or entry['sha256']!=figure['sha256']:
            raise ValueError('Prior pixel QA cannot be reused')
        review=next(r for r in reviewed['figure_reviews'] if r['id']==figure['id'])
        if not all(review[k] for k in ('axes_units','legend','aggregation_n','quantitative_observation','limitations')):
            raise ValueError('Caption content review incomplete')
    matrix=load('report/phase08/question_evidence_matrix.json')
    if len(matrix)!=10 or [q['number'] for q in matrix]!=list(range(1,11)):
        raise ValueError('Question matrix incomplete')
    for question in matrix:
        if question['heading'] not in text or not question['artifacts'] or not question['resolved_code']:
            raise ValueError('Question evidence incomplete')
        for code in question['resolved_code']:
            if code!=extract_code(BASE,code['path'],code['symbol']):
                raise ValueError('Question code locator changed')
    citation_ids=set(re.findall(r'\b[SD]\d\b',text))
    if citation_ids!={*[f'S{i}' for i in range(1,8)],*[f'D{i}' for i in range(2,8)]}:
        raise ValueError('Unexpected/missing source attribution IDs')
    if not all(value in text for value in ('B23DCCN053','D23CTPM01','2501.06322v1','10.1109/ACCESS.2020.3038605')):
        raise ValueError('Academic or student identifier corrupted')
    calc=calculations()
    tests=ET.parse(BASE/'evidence/phase08/final_tests_r2.xml').getroot()
    count=len(tests.findall('.//testcase'))
    coverage=load('evidence/phase08/final_coverage_r2.json')['totals']
    quality=load('evidence/phase08/quality_checks.json')
    if count!=234 or any(tests.findall('.//'+k) for k in ('failure','error','skipped')) or coverage['percent_covered']<80:
        raise ValueError('Content helper tests/coverage failed')
    if quality['status']!='PASS' or any(quality['exit_codes'].values()):
        raise ValueError('Lint/CLI check failed')
    receipt={**structure,'status':'PASS','phase':8,'tables':len(book['tables']),'code_excerpts':len(excerpts),
        'numeric_tokens_used':len([k for k in used if k.startswith('N.')]),'numeric_source_records':len(book['numbers']),
        'input_files':len(index),'question_evidence_rows':10,'saved_arithmetic_checks':len(calc['checks']),
        'prior_protected_files_preserved':len(old),'selected_parent_assets_preserved':len(parent['preservation']),
        'tests_passed':count,'skipped':0,'coverage_combined_percent':coverage['percent_covered'],
        'test_evidence':'evidence/phase08/final_tests_r2.xml','coverage_evidence':'evidence/phase08/final_coverage_r2.json',
        'coverage_scope':'report_assets helper only; excludes manuscript prose,compiler/auditor and scientific code',
        'scientific_forward_added':0,'train_runs_added':0,'docx_pdf_rendered':False,'next_phase':9,
        'manuscript_sha256':sha256_file(OUT/'manuscript.md'),'word_count_whitespace':len(text.split())}
    return receipt,calc


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal',action='store_true')
    args=parser.parse_args()
    with (BASE/'evidence/phase03/.writer.lock').open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        receipt,calc=audit()
        if args.seal:
            save('report/phase08/calculation_checks.json',calc)
        elif load('report/phase08/calculation_checks.json')!=calc:
            raise ValueError('Saved arithmetic evidence changed')
        paths=[BASE/p for p in ('compile_phase08.py','verify_phase08.py','code/report_assets.py','tests/test_phase08.py',
            'tests/coverage_phase08.ini','docs/phase08_report.md','docs/phase08_operations.md','report/question_evidence_matrix.md',
            'evidence/phase07/experiment_lock.json')]
        for folder in (OUT,BASE/'evidence/phase08'):
            paths += [p for p in folder.rglob('*') if p.is_file() and p.name not in
                ('.coverage','experiment_lock.json','verification.json','active_controller.json')]
        lock={'schema':'ag02.phase08.content_release.1','files':[{'path':p.relative_to(BASE).as_posix(),
            'sha256':sha256_file(p),'bytes':p.stat().st_size} for p in sorted(set(paths))]}
        if args.seal:
            save('evidence/phase08/experiment_lock.json',lock)
        elif load('evidence/phase08/experiment_lock.json')!=lock:
            raise ValueError('Content release changed')
        receipt.update({'locked_files':len(lock['files']),'experiment_lock_sha256':sha256_file(BASE/'evidence/phase08/experiment_lock.json')})
        if args.seal:
            save('evidence/phase08/verification.json',receipt)
        elif load('evidence/phase08/verification.json')!=receipt:
            raise ValueError('Verification changed')
        print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
