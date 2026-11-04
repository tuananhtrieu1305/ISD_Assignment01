"""Apply explicit assistant support review to saved outputs; no inference or source tuning."""
from pathlib import Path
import hashlib
import json
import os
import sys

for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'web/backend'))
from project01_core.evaluation import apply_support_reviews,plot_results,read_results,summarize

ASSESSMENTS={
 'knowledge_00':('partial','Source is specifically proximal neuropathy; the standalone answer uses “This type” without its antecedent.'),
 'knowledge_01':('partial','The extracted “proliferative retinopathy” is a fragment; it does not explain the requested topic.'),
 'knowledge_02':('partial','The three presentations refer to brittle diabetes in the source; the extracted answer omits that scope.'),
 'knowledge_03':('supported','The complete statement about insulin in type1 diabetes is explicitly present in the cited source.'),
 'knowledge_04':('unsupported','Question concerns type1; answer concerns type2 and ends mid-sentence.'),
 'knowledge_05':('supported','A complete source statement identifies type1 and type2 as common forms; relevant to the broad topic question.'),
 'knowledge_06':('supported','The gestational-diabetes statement is present verbatim in the preserved source; not a current clinical validation.'),
 'knowledge_07':('supported','The source explicitly gives the A1C/BP/cholesterol mnemonic; a limited but on-topic statement.'),
 'combined_00':('supported','The complete pancreas/insulin statement is directly supported by the cited snapshot; score is a separate model output.'),
 'combined_01':('supported','The ABC mnemonic is explicitly in the cited text and includes cholesterol; the broad topic allows this limited fact.'),
 'combined_02':('supported','The medication statement is a verbatim historical source excerpt, not individualized treatment from the survey score.'),
 'combined_03':('supported','The source explicitly states that some people with diabetes have no symptoms.'),
 'combined_04':('supported','The cited context identifies diabetes as the subject and explicitly includes vision loss among complications.'),
 'combined_05':('supported','The cited document explicitly reports the oral glucose tolerance test use quoted in the answer.'),
 'combined_06':('supported','The complete preserved statement includes kidney failure among complications associated with the topic.'),
 'combined_07':('partial','“Learn more about prediabetes here” is navigation text, not an informative answer.'),
 'fault_00':('partial','The recovered citation may match the phrase, but “Learn more … here” still does not explain diabetes.'),
 'fault_01':('partial','“Learn more … here” is not an informative explanation; numeric tampering is evaluated separately.'),
}

def main():
    base=PROJECT/'artifacts/phase2/evaluation'
    if (base/'raw_results').exists():raise RuntimeError('Already reviewed; never overwrite raw/derived results')
    rows=read_results(base/'results');assert len(rows)==120
    reviews=[];signatures={}
    for row in rows:
        if not row['metrics']['support_review_required']:continue
        suffix=row['case_id'].removeprefix('p01_evaluation_')
        rating,reason=ASSESSMENTS[suffix]
        knowledge=row['result']['knowledge'];cited=[r for r in knowledge['evidence'] if r['chunk_id'] in knowledge['citations']]
        signature=(knowledge['answer'],tuple((r['chunk_id'],r['text']) for r in cited))
        if row['category']!='fault':
            if row['case_id'] in signatures:assert signature==signatures[row['case_id']],row['case_id']
            signatures[row['case_id']]=signature
        if suffix=='fault_00' and row['variant'] in {'P0','P1'}:
            rating='unsupported';reason='Injected citation refers to a different valid medical chunk that does not contain/support the extracted answer.'
        reviews.append({'case_id':row['case_id'],'variant':row['variant'],'rating':rating,'reason':reason,'reviewer':'Codex assistant','review_kind':'manual reading of saved answer and cited source, not independent human/clinical review','answer':knowledge['answer'],'evidence_locators':[r['document_id']+'/'+r['chunk_id'] for r in cited],'scope':'support and answer adequacy relative to the preserved snapshot; not current medical guidance'})
    assert len(reviews)==54
    review={'version':'project01.support-review.1','reviewer':'Codex assistant','independent_human_review':False,'clinical_validation':False,'date':'2026-11-01','rows':reviews}
    (PROJECT/'artifacts/phase2/support_reviews.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
    reviewed=apply_support_reviews(rows,reviews)
    original={p.stem:hashlib.sha256(p.read_bytes()).hexdigest() for p in (base/'results').glob('*.json')}
    # Preserve exact raw bytes; publish a separate derived metrics revision at the active read path.
    (base/'results').rename(base/'raw_results');(base/'results').mkdir()
    for row in reviewed:
        key=row['case_id']+'_'+row['variant']
        row['derived_from']={'path':'artifacts/phase2/evaluation/raw_results/'+key+'.json','sha256':original[key],'transformation':'append manual support and final task-success labels only; model/tool/trace outputs unchanged'}
        raw=json.loads((base/'raw_results'/(key+'.json')).read_text())
        assert row['result']==raw['result'] and row['metrics']['automatic_success']==raw['metrics']['automatic_success']
        with (base/'results'/(key+'.json')).open('x') as stream:json.dump(row,stream,ensure_ascii=False,indent=2,allow_nan=False)
    summary=summarize(reviewed)
    (PROJECT/'artifacts/phase2/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    (base/'reviewed.json').write_text(json.dumps({'status':'COMPLETE','raw_outputs':120,'derived_outputs':120,'reviews':54,'evaluation_executions_per_case_variant':1,'new_pipeline_calls_in_postprocessing':0},indent=2)+'\n')
    plot_results(reviewed,PROJECT/'report/figures')
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
