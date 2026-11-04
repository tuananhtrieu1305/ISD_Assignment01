"""Data-only seed revision; retain the first curated seed unchanged."""
from pathlib import Path
import json
from collections import defaultdict

P=Path(__file__).resolve().parents[2]
K=P/'artifacts/llm_v2/kg'
D=P/'datasets/llm_v2'


def main():
    target=K/'seed_r2.json'
    if target.exists():raise RuntimeError('Revision exists')
    seed=json.loads((K/'seed_v1.json').read_text(encoding='utf-8'))
    parents={r['qa_id']:r for r in map(json.loads,(D/'qa_context.jsonl').read_text(encoding='utf-8').splitlines())}
    chunks=list(map(json.loads,(D/'chunks.jsonl').read_text(encoding='utf-8').splitlines()))
    specs=[
        ('type1','CHARACTERIZED_BY','beta_cells','mq-1a96cc5a67a19f40-qa1','Type 1 diabetes is caused by a lack of insulin due to the destruction of insulin-producing beta cells in the pancreas.','destruction of insulin-producing cells'),
        ('diabetes','MAY_DAMAGE','kidney_damage','mq-39edc72b4c07d38d-qa0','Diabetic kidney disease, also called diabetic nephropathy, is kidney disease caused by diabetes.','diabetic nephropathy definition'),
        ('urine_test','ASSESSES','kidney_damage','mq-39edc72b4c07d38d-qa4','A health care provider diagnoses diabetic kidney disease based on - a medical and family history - a physical exam - urine tests - a blood test','part of clinical assessment, not sufficient alone'),
        ('blood_test','ASSESSES','kidney_damage','mq-39edc72b4c07d38d-qa4','A health care provider diagnoses diabetic kidney disease based on - a medical and family history - a physical exam - urine tests - a blood test','part of clinical assessment'),
        ('activity','SUPPORTS','kidney_damage','mq-39edc72b4c07d38d-qa6','People can prevent or slow the progression of diabetic kidney disease by - taking medications to control high blood pressure - managing blood glucose levels - making changes in their eating, diet, and nutrition - losing weight if they are overweight or obese - getting regular physical activity','supports prevention/slowing; not cure, read full source'),
        ('retinopathy','CHARACTERIZED_BY','early_asymptomatic','mq-87817109141185fc-qa4','If you have diabetic retinopathy, at first you may notice no changes to your vision.','early stage; may notice no change'),
        ('diabetes','INCREASES_RISK_OF','heart_disease','mq-281b438f8f3b0193-qa0','If you have diabetes or pre-diabetes you have an increased risk for heart disease.','diabetes or prediabetes to heart disease'),
        ('diabetes','MAY_DAMAGE','neuropathy','mq-f759555ecf86b7f3-qa0','If you have diabetes, your blood glucose, or blood sugar, levels are too high. Over time, this can damage the covering on your nerves or the blood vessels that bring oxygen to your nerves.','over time; high glucose damages nerve covering or blood supply'),
        ('glucose','SUPPORTS','neuropathy','mq-f2d73ab83304811e-qa8','Maintaining safe blood glucose levels protects nerves throughout the body.','safe glycemic levels support nerve protection, not elevated glucose'),
    ]
    for spec in specs:
        sub,rel,obj,qid,quote,condition=spec
        q=parents[qid];start=q['answer'].index(quote)
        hits=[c['chunk_id'] for c in chunks if quote in c['content'] and any(r['qa_id']==qid for r in c['source_refs'])]
        assert hits
        seed['relationships'].append({'id':f"kg2-a{len(seed['relationships'])+1:03}",'subject':sub,'relation':rel,'object':obj,
            'direction':'subject_to_object','polarity':'negative' if obj=='early_asymptomatic' else 'positive','conditions':condition,
            'source_qa_id':qid,'document_id':q['document_id'],'source_chunk_ids':hits,'quote':quote,
            'answer_start':start,'answer_end':start+len(quote),'source_url':q['source_url'],'snapshot_url':q['snapshot_url'],
            'review':{'status':'SOURCE_CHECKED_ASSISTANT','reviewer':'Codex assistant','date':'2026-11-02',
                      'not_clinical_expert_review':True,'direction_and_scope_note':condition}})
    seed['schema_version']='kg-seed-r2'
    seed['parent_revision']='seed_v1.json'
    adjacency=defaultdict(list)
    for a in seed['relationships']:adjacency[a['subject']].append({'assertion_id':a['id'],'relation':a['relation'],'target':a['object']})
    stats={'entities':len(seed['entities']),'assertions':len(seed['relationships']),
           'connected_entities':len({a[t] for a in seed['relationships'] for t in ['subject','object']}),
           'source_qa_contexts':len({a['source_qa_id'] for a in seed['relationships']}),
           'source_documents':len({a['document_id'] for a in seed['relationships']}),
           'unique_source_chunks':len({c for a in seed['relationships'] for c in a['source_chunk_ids']}),
           'automatic_extraction_calls':0,'all_assertions_source_checked_by_assistant':True,
           'runtime_graph_retrieval_implemented':False}
    for path,value in [(target,seed),(K/'adjacency_seed_r2.json',dict(adjacency)),(K/'seed_stats_r2.json',stats)]:
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(stats))


if __name__=='__main__':main()
