"""Assemble Vietnamese Agent02 report from frozen artifacts and authored text; no model execution."""

import csv
import json
import statistics
from pathlib import Path

from .code.report_assets import (
    decimal_vi,
    extract_code,
    markdown_table,
    readable_prose,
    render_tokens,
    validate_structure,
)
from .workspace import sha256_file

BASE=Path(__file__).resolve().parent
OUT='report/phase08'
CONFIGS=('baseline','alpha_low','alpha_high','epsilon_low_fixed','epsilon_high_fixed')
LABELS={'baseline':'Baseline (α0,10; ε giảm)','alpha_low':'α0,01','alpha_high':'α0,50',
        'epsilon_low_fixed':'ε cố định0,05','epsilon_high_fixed':'ε cố định0,30'}
FIGURES=[(3,n) for n in ('ref_learning_curve','controlled_learning_curve','q_tables','action_counts')]+[
    (4,n) for n in ('alpha_curves','exploration_curves','epsilon_schedules','train_summary')]+[
    (5,n) for n in ('final_profit','paired_and_match','train_vs_final','discount_rates')]+[
    (6,n) for n in ('gold_calibration','two_learner_training','checkpoint_drift','variant_robustness')]+[
    (7,n) for n in ('augmented_training','augmented_final_profit','augmented_paired_delta','augmented_coverage_cost')]
EXCERPTS=[('E01','code/controlled.py','RuleAgent.act',{}),('E02','code/controlled.py','QAgent.act',{}),
    ('E03','code/controlled.py','QAgent.learn',{}),('E04','code/training.py','TrainSession.run_chunk',
     {'start':'            for step in range(self.market.steps):','end':'                total += result.rewards'}),
    ('E05','code/evaluation/final_v1.py','evaluate_tapes',
     {'end':'        learner.q.flags.writeable = False'}),
    ('E06','code/evaluation/final_v1.py','evaluate_tapes',
     {'start':"    after = q_digest(q) if kind == 'q' else None",'end':"        raise RuntimeError('Frozen Q changed')"}),
    ('E07','phase06.py','markets',{}),('E08','code/augmented.py','AugmentedAgent.learn',{})]


def assets():
    inputs={}
    numbers={}
    tokens={}
    def register(path):
        target=BASE/path
        inputs[path]={'path':path,'bytes':target.stat().st_size,'sha256':sha256_file(target)}
        return target
    def js(path):
        return json.loads(register(path).read_text(encoding='utf-8'))
    def cs(path):
        with register(path).open(encoding='utf-8') as stream:
            return list(csv.DictReader(stream))
    def add(key,value,path,locator,*,digits=5,kind='measured'):
        formatted=decimal_vi(value,digits)
        numbers[key]={'value':float(value),'formatted':formatted,'source':path,'locator':locator,'kind':kind}
        tokens['N.'+key]=formatted
    def fields(prefix,row,path):
        for field,value in row.items():
            if isinstance(value,bool):
                continue
            try:
                number=float(value)
            except (TypeError,ValueError):
                continue
            add(prefix+'.'+field,number,path,{'row':prefix,'field':field})
    p3='artifacts/metrics/phase03_train_summary.csv'
    train3=cs(p3)
    for row in train3:
        fields('train3.'+row['track'],row,p3)
        for agent in ('rl','rule'):
            for index,value in enumerate(json.loads(row[agent+'_action_counts'])):
                add(f'train3.{row["track"]}.{agent}_action{index}',value,p3,{'track':row['track'],'field':agent+'_action_counts','index':index},digits=0)
    p4='artifacts/metrics/phase04/config_train_summary.csv'
    train4={r['config_id']:r for r in cs(p4)}
    for config,row in train4.items():
        fields('train4.'+config,row,p4)
    p5='artifacts/metrics/phase05/config_summary.json'
    final5={r['config_id']:r for r in js(p5)}
    for config,row in final5.items():
        fields('final5.'+config,row,p5)
        add('final5.'+config+'.discount_percent',100*row['discount_rate_mean'],p5,{'config_id':config,'field':'discount_rate_mean','scale':100},digits=3)
    controls=js('artifacts/metrics/phase05/controls_summary.json')
    add('rule_control_mean',statistics.mean(r['target_mean'] for r in controls if r['kind']=='rule'),
        'artifacts/metrics/phase05/controls_summary.json',{'kind':'rule','operation':'mean(target_mean)'})
    pb='artifacts/metrics/phase05/baseline_reward.csv'
    baseline=cs(pb)
    for row in baseline:
        fields('baseline.s'+row['train_seed'],row,pb)
        for name in ('target_total','opponent_total','steps'):
            add('baseline.s'+row['train_seed']+'.'+name+'_int',float(row[name]),pb,
                {'track':row['track'],'seed':row['train_seed'],'field':name},digits=0)
    pv='artifacts/metrics/phase06/variant_summary.csv'
    variants={(r['kernel'],r['policy']):r for r in cs(pv)}
    for (kernel,policy),row in variants.items():
        fields(f'variant.{kernel}.{policy}',row,pv)
    pd='artifacts/metrics/phase06/variant_deltas.csv'
    variant_deltas=cs(pd)
    for kernel in ('persistent','gold'):
        values=[float(r['retrained_minus_baseline']) for r in variant_deltas if r['kernel']==kernel]
        for name,value in [('mean',statistics.mean(values)),('std',statistics.stdev(values))]:
            add(f'variant_delta.{kernel}.{name}',value,pd,{'kernel':kernel,'field':'retrained_minus_baseline','operation':name})
    pq='artifacts/metrics/phase06/q8_summary.csv'
    q8=cs(pq)
    for row in q8:
        fields('q8.e'+row['checkpoint_episode'],row,pq)
    pdrift='artifacts/metrics/phase06/policy_drift.csv'
    drift=cs(pdrift)
    add('drift.changed',sum(int(r['greedy_action_sets_changed_of4']) for r in drift),pdrift,
        {'operation':'sum(greedy_action_sets_changed_of4)'},digits=0)
    add('drift.intervals',len(drift),pdrift,{'operation':'row_count'},digits=0)
    ppair='artifacts/metrics/phase06/train_summary.csv'
    pair_rows=cs(ppair)
    for agent in (0,1):
        selected=[float(r['train_mean']) for r in pair_rows if int(r['learners'])==2 and int(r['agent'])==agent]
        add(f'pairtrain.agent{agent}.mean',statistics.mean(selected),ppair,
            {'learners':2,'agent':agent,'operation':'mean(train_mean)'})
    pg='data/derived/gold_regime_kernel_v1.json'
    gold=js(pg)
    for i in (0,1):
        for j in (0,1):
            add(f'gold.p{i}{j}',gold['kernel'][i][j],pg,{'field':'kernel','index':[i,j]},digits=6)
            add(f'gold.n{i}{j}',gold['transition_counts'][i][j],pg,{'field':'transition_counts','index':[i,j]},digits=0)
    add('gold.months',gold['valid_prices'],pg,{'field':'valid_prices'},digits=0)
    add('gold.regimes',sum(gold['regime_counts']),pg,{'operation':'sum(regime_counts)'},digits=0)
    add('gold.transitions',sum(sum(r) for r in gold['transition_counts']),pg,{'operation':'sum(transition_counts)'},digits=0)
    pa='artifacts/metrics/phase07/policy_summary.csv'
    improved={(r['kernel'],r['policy']):r for r in cs(pa)}
    for (kernel,policy),row in improved.items():
        fields(f'improved.{kernel}.{policy}',row,pa)
    pdelta='artifacts/metrics/phase07/delta_summary.csv'
    deltas={r['kernel']:r for r in cs(pdelta)}
    for kernel,row in deltas.items():
        fields('delta.'+kernel,row,pdelta)
    po='artifacts/metrics/phase07/oracle_summary.csv'
    oracle=cs(po)
    for row in oracle:
        fields('oracle.'+row['kernel'],row,po)
    pcost='artifacts/metrics/phase07/cost_coverage.csv'
    cost_rows=cs(pcost)
    for kernel in ('iid','persistent','gold'):
        selected=[r for r in cost_rows if r['kernel']==kernel and r['policy']=='augmented']
        add('coverage.'+kernel,100*statistics.mean(float(r['visited_fraction']) for r in selected),pcost,
            {'kernel':kernel,'policy':'augmented','operation':'100*mean(visited_fraction)'},digits=1)
    pmodel='artifacts/metrics/phase07/model_expectations.csv'
    model=cs(pmodel)
    for kernel in ('iid','persistent','gold'):
        values=[float(r['exact_expected_profit_per_step_gamma1']) for r in model if r['kernel']==kernel and r['policy']=='augmented']
        add('model.'+kernel+'.augmented_mean',statistics.mean(values),pmodel,
            {'kernel':kernel,'policy':'augmented','field':'exact_expected_profit_per_step_gamma1','operation':'mean'},kind='analytic_known_model')
    policy_rows=[]
    for track,run in [('REF','ref/baseline/s0042'),('CONTROLLED','controlled/iid/baseline/s0011')]:
        path=f'artifacts/runs/{run}/policy.json'
        for row in js(path):
            policy_rows.append([track,str(tuple(row['state'])),decimal_vi(row['q_no_discount'],2),
                                decimal_vi(row['q_discount'],2),'/'.join(str(a) for a in row['greedy_action_set'])])
    tables={}
    def table(name,headers,rows,sources):
        text=markdown_table(headers,rows)
        tables[name]={'headers':headers,'rows':rows,'sources':sources,'markdown':text}
        tokens['T.'+name]=text
    table('baseline_train',['Track/seed','Agent','Total profit','Profit/bước','Giữ giá','Giảm giá'],[
        [row['track']+'/'+row['seed'],agent.upper(),decimal_vi(row[agent+'_total_reward'],0,group=True),
         decimal_vi(row[agent+'_mean_reward_per_step']),*[decimal_vi(v,0,group=True) for v in json.loads(row[agent+'_action_counts'])]]
        for row in train3 for agent in ('rl','rule')],[p3])
    table('q_policy',['Track','State (nhu cầu,đối thủ trước)','Q giữ giá','Q giảm giá','Greedy action'],policy_rows,
        ['artifacts/runs/ref/baseline/s0042/policy.json','artifacts/runs/controlled/iid/baseline/s0011/policy.json'])
    def paired(mean,std):
        return decimal_vi(mean)+' ± '+decimal_vi(std)
    for name,configs in [('alpha',CONFIGS[:3]),('exploration',(CONFIGS[0],*CONFIGS[3:]))]:
        table(name,['Cấu hình','Train Q mean±std','Final Q mean±std'],[
            [LABELS[c],paired(train4[c]['rl_train_mean'],train4[c]['rl_train_std']),paired(final5[c]['target_mean'],final5[c]['target_std'])]
            for c in configs],[p4,p5])
    table('core_final',['Cấu hình','Q final mean±std','Rule cùng trận mean±std','Q−rule cùng trận','Q−policy rule'],[
        [LABELS[c],paired(final5[c]['target_mean'],final5[c]['target_std']),paired(final5[c]['opponent_mean'],final5[c]['opponent_std']),
         decimal_vi(final5[c]['within_match_delta_mean']),decimal_vi(final5[c]['delta_vs_rule_policy_mean'])] for c in CONFIGS],[p5])
    table('baseline_final',['Track/seed','Profit Q','Profit rule','Tổng reward Q','Tổng reward rule','Bước gộp vai'],[
        [r['track']+'/'+r['train_seed'],decimal_vi(r['target_mean']),decimal_vi(r['opponent_mean']),
         decimal_vi(r['target_total'],0,group=True),decimal_vi(r['opponent_total'],0,group=True),decimal_vi(r['steps'],0,group=True)] for r in baseline],[pb])
    table('q8',['Checkpoint episode','Mean profit/bước ±std qua5pair seed'],[
        [r['checkpoint_episode'],paired(r['target_mean'],r['target_std'])] for r in q8],[pq])
    table('gold_kernel',['Regime hiện tại','Count →0','Count →1','P →0 sau cộng1','P →1 sau cộng1'],[
        [i,gold['transition_counts'][i][0],gold['transition_counts'][i][1],decimal_vi(gold['kernel'][i][0],6),decimal_vi(gold['kernel'][i][1],6)] for i in (0,1)],[pg])
    table('variants',['Kernel','Q IID cũ mean±std','Q train lại mean±std','Rule mean±std'],[
        [k,*[paired(variants[k,p]['target_mean'],variants[k,p]['target_std']) for p in ('baseline_iid','retrained','rule')]]
        for k in ('persistent','gold')],[pv])
    table('improved',['Kernel','Memory/time mean±std','Baseline cùngkernel mean±std','Rule mean±std'],[
        [k,*[paired(improved[k,p]['profit_mean'],improved[k,p]['profit_std']) for p in ('augmented','baseline','rule')]]
        for k in ('iid','persistent','gold')],[pa])
    table('improved_delta',['Kernel','Memory/time−baseline mean±std','Memory/time−rule mean±std'],[
        [k,paired(deltas[k]['delta_vs_baseline_mean'],deltas[k]['delta_vs_baseline_std']),
         paired(deltas[k]['delta_vs_rule_mean'],deltas[k]['delta_vs_rule_std'])] for k in ('iid','persistent','gold')],[pdelta])
    table('oracle',['Kernel','Oracle expected profit/bước (γ1)','Memory/time expected profit/bước'],[
        [r['kernel'],decimal_vi(r['optimal_expected_profit_per_step_gamma1']),tokens['N.model.'+r['kernel']+'.augmented_mean']]
        for r in oracle],[po,pmodel])
    excerpts=[]
    for key,path,symbol,options in EXCERPTS:
        register(path)
        value={'id':key,**extract_code(BASE,path,symbol,**options)}
        excerpts.append(value)
        tokens['C.'+key]=('```python\n'+value['text']+'\n```\n\nNguồn '+key+': `'+path+'`, dòng '+str(value['start_line'])+'–'+str(value['end_line'])+
            '; SHA256 `'+value['source_sha256'][:16]+'…` (hash đầy đủ trong code_excerpt_index.json).')
    figures=[]
    for index,(phase,name) in enumerate(FIGURES,1):
        path=f'artifacts/figures/phase{phase:02d}/{name}.png'
        notes_path=f'artifacts/figures/phase{phase:02d}/figure_notes.json'
        register(path)
        register(notes_path)
        figures.append({'id':f'F{index:02d}','phase':phase,'path':path,'sha256':inputs[path]['sha256'],'notes_path':notes_path})
        tokens[f'I.F{index:02d}']=f'![F{index:02d}](../../{path})'
    for path in ('sources/manifest.json','docs/protocol_v1.json','docs/requirements.md'):
        register(path)
    for row in js('sources/manifest.json'):
        register('sources/provided/'+row['name'])
    return {'tokens':tokens,'numbers':numbers,'tables':tables,'excerpts':excerpts,'figures':figures,'inputs':inputs}


def compile_report():
    release=BASE/'evidence/phase08/experiment_lock.json'
    if release.exists():
        for item in json.loads(release.read_text())['files']:
            if sha256_file(BASE/item['path'])!=item['sha256']:
                raise ValueError('Released content changed; create a versioned revision')
        print(json.dumps({'status':'REUSED_RELEASE_NO_WRITE','scientific_forward_added':0,'train_runs_added':0}))
        return
    book=assets()
    template=BASE/'report/phase08/source_template.md'
    text,used=render_tokens(readable_prose(template.read_text(encoding='utf-8')),book['tokens'])
    text=readable_prose(text)
    structure=validate_structure(text)
    for figure in book['figures']:
        marker=f'![{figure["id"]}]'
        position=text.index(marker)
        start=text.index('\n',position)
        figure['caption_text']=' '.join(text[start:].lstrip().split('\n\n',1)[0].split())
        figure['caption_review_scope']='Author reviewed axes,legend,aggregation,n,quantitative observation and limits; original pixel QA preserved in prior phase'
    out=BASE/OUT
    out.mkdir(parents=True,exist_ok=True)
    (out/'manuscript.md').write_text(text,encoding='utf-8')
    def save(name,value):
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    save('numeric_claims.json',book['numbers'])
    save('tables.json',book['tables'])
    save('code_excerpt_index.json',book['excerpts'])
    save('figure_catalog.json',book['figures'])
    design_path=BASE/'report/phase08/evidence_design.json'
    design=json.loads(design_path.read_text(encoding='utf-8'))
    matrix=[]
    for question in design['questions']:
        if question['heading'] not in text:
            raise ValueError('Question answer heading missing:'+question['id'])
        symbols=[]
        for code in question['code']:
            symbols.append(extract_code(BASE,code['path'],code['symbol']))
        for path in [c['path'] for c in question['code']]+question['artifacts']:
            target=BASE/path
            book['inputs'][path]={'path':path,'bytes':target.stat().st_size,'sha256':sha256_file(target)}
        if any(t not in book['tables'] for t in question['tables']) or any(f not in {r['id'] for r in book['figures']} for f in question['figures']):
            raise ValueError('Unknown question evidence table/figure')
        matrix.append({**question,'resolved_code':symbols,'manuscript':'report/phase08/manuscript.md'})
    save('question_evidence_matrix.json',matrix)
    matrix_text='# AG02 — đối chiếu đủ10câu với bằng chứng\n\nBản thảo: [manuscript.md](phase08/manuscript.md). Code/CSV/hình được đọc từ các khóa Phase1–7;không có train/final mới.\n\n'
    for q in matrix:
        matrix_text+=f'## {q["id"]} — {q["heading"]}\n\n'+q['claim']+'\n\n'
        matrix_text+='Code: '+'; '.join(f'`{c["path"]}:{c["start_line"]}` {c["symbol"]}' for c in q['resolved_code'])+'.\n\n'
        matrix_text+='Bảng: '+', '.join(q['tables'])+';hình: '+', '.join(q['figures'])+';nguồn: '+', '.join(q['literature'])+'.\n\n'
        matrix_text+='Artifact: '+'; '.join('`'+p+'`' for p in q['artifacts'])+'.\n\n'
    (BASE/'report/question_evidence_matrix.md').write_text(readable_prose(matrix_text),encoding='utf-8')
    book['inputs']['report/phase08/evidence_design.json']={'path':'report/phase08/evidence_design.json',
        'bytes':design_path.stat().st_size,'sha256':sha256_file(design_path)}
    inputs=list(book['inputs'].values())+[{'path':'report/phase08/source_template.md','sha256':sha256_file(template),'bytes':template.stat().st_size}]
    save('input_index.json',inputs)
    receipt={**structure,'status':'COMPILED_PENDING_CONTENT_AUDIT','numeric_tokens_used':len([k for k in used if k.startswith('N.')]),
        'tables':len(book['tables']),'code_excerpts':len(book['excerpts']),'input_files':len(inputs),
        'manuscript_sha256':sha256_file(out/'manuscript.md'),'word_count_whitespace':len(text.split()),
        'question_evidence_rows':len(matrix),'theory_formula_policy':'Q-update,required Q3 arithmetic,margin and mean reward only; no unnecessary derivations',
        'scientific_forward_added':0,'train_runs_added':0,'rendered_docx_or_pdf':False}
    save('build_receipt.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False,indent=2))


if __name__=='__main__':
    compile_report()
