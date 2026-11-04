"""Phase-1 data curation, not the Phase-2 group KG/retrieval implementation."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json

PROJECT = Path(__file__).resolve().parents[2]
DATA = PROJECT / 'datasets/llm_v2'
OUT = PROJECT / 'artifacts/llm_v2/kg'


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'seed_v1.json').exists():
        raise RuntimeError('Seed exists; use a revision, do not overwrite')
    parents = {r['qa_id']: r for r in rows(DATA / 'qa_context.jsonl')}
    chunks = rows(DATA / 'chunks.jsonl')
    # Canonical bilingual aliases are curated metadata, not generated translations.
    definitions = [
        ('diabetes','Disease','Diabetes mellitus','tiểu đường|đái tháo đường|diabetes mellitus'),
        ('type1','Subtype','Type 1 diabetes','tiểu đường type 1|đái tháo đường típ 1|type 1 diabetes'),
        ('type2','Subtype','Type 2 diabetes','tiểu đường type 2|đái tháo đường típ 2|type 2 diabetes'),
        ('gestational','Subtype','Gestational diabetes','tiểu đường thai kỳ|gestational diabetes'),
        ('prediabetes','MedicalConcept','Prediabetes','tiền tiểu đường|tiền đái tháo đường|prediabetes'),
        ('insulin','MedicalConcept','Insulin','insulin'),
        ('insulin_resistance','MedicalConcept','Insulin resistance','kháng insulin|insulin resistance'),
        ('pancreas','MedicalConcept','Pancreas','tuyến tụy|pancreas'),
        ('beta_cells','MedicalConcept','Beta cells','tế bào beta|beta cells'),
        ('glucose','MedicalConcept','Blood glucose','đường huyết|đường máu|blood glucose|blood sugar'),
        ('kidney_damage','Complication','Diabetic kidney disease','bệnh thận do tiểu đường|bệnh thận|diabetic nephropathy|kidney disease'),
        ('heart_disease','Complication','Heart disease','bệnh tim|heart disease'),
        ('stroke','Complication','Stroke','đột quỵ|stroke'),
        ('neuropathy','Complication','Diabetic neuropathy','bệnh thần kinh do tiểu đường|diabetic neuropathy|nerve damage'),
        ('retinopathy','Complication','Diabetic retinopathy','bệnh võng mạc tiểu đường|diabetic retinopathy'),
        ('retina','MedicalConcept','Retinal blood vessels','mạch máu võng mạc|retina'),
        ('foot_sensation','Symptom','Loss of foot sensation','mất cảm giác bàn chân|lose feeling in your feet'),
        ('foot_blood_supply','MedicalConcept','Inadequate foot blood supply','thiếu máu bàn chân|feet do not get enough blood'),
        ('obesity','RiskFactor','Obesity','béo phì|obese|obesity'),
        ('family_history','RiskFactor','Family history of diabetes','tiền sử gia đình|family history of diabetes'),
        ('inactivity','RiskFactor','Physical inactivity','ít vận động|không tập thể dục|do not exercise'),
        ('older_age','RiskFactor','Older age','tuổi cao|older'),
        ('activity','Lifestyle','Physical activity','vận động|tập thể dục|physical activity|exercise'),
        ('healthy_weight','MedicalConcept','Healthy weight','cân nặng hợp lý|healthy weight'),
        ('healthy_eating','Lifestyle','Healthy eating','ăn uống lành mạnh|healthy eating'),
        ('dietitian','MedicalConcept','Registered dietitian','chuyên gia dinh dưỡng|dietitian'),
        ('meal_plan','Lifestyle','Individual eating plan','kế hoạch ăn uống|eating plan|meal plan'),
        ('a1c','Test','A1C test','hba1c|a1c'),
        ('urine_test','Test','Urine tests','xét nghiệm nước tiểu|urine tests'),
        ('blood_test','Test','Blood test','xét nghiệm máu|blood test'),
        ('thirst','Symptom','Increased thirst','khát nhiều|increased thirst'),
        ('urination','Symptom','Frequent urination','tiểu nhiều|frequent urination'),
        ('blurred_vision','Symptom','Blurred vision','nhìn mờ|blurred vision'),
        ('edema','Symptom','Edema','phù|edema'),
        ('early_asymptomatic','Symptom','No early symptoms','không có triệu chứng sớm|no symptoms in the early stages'),
    ]
    entities = [{'id': key, 'type': typ, 'name': name, 'aliases': aliases.split('|')}
                for key, typ, name, aliases in definitions]
    # Each row is an explicitly reviewed assertion. One quote can support several
    # distinct edges, but endpoints/predicate retain the original direction.
    specs = [
        ('type1','SUBTYPE_OF','diabetes','mq-cdb161eaa3dbc89d-qa0','With type 1 diabetes, your body does not make insulin.', 'type1', 'positive', 'Concept taxonomy and type-1 qualifier'),
        ('type2','SUBTYPE_OF','diabetes','mq-cdb161eaa3dbc89d-qa0','With type 2 diabetes, the more common type, your body does not make or use insulin well.', 'type2', 'positive', 'Concept taxonomy and type-2 qualifier'),
        ('gestational','SUBTYPE_OF','diabetes','mq-cdb161eaa3dbc89d-qa0','Pregnant women can also get diabetes, called gestational diabetes.', 'pregnancy', 'positive', 'Pregnancy-specific subtype'),
        ('type1','CHARACTERIZED_BY','insulin','mq-66c3595f48e5fa69-qa0','With type 1 diabetes, your pancreas does not make insulin.', 'pancreas does not make insulin', 'negative', 'Negative qualifier applies to insulin production; NOT absence of disease'),
        ('insulin','SUPPORTS','glucose','mq-66c3595f48e5fa69-qa0','Insulin is a hormone that helps glucose get into your cells to give them energy.', 'cellular glucose uptake', 'positive', 'Function, not a claim that insulin raises blood glucose'),
        ('insulin_resistance','CHARACTERIZED_BY','insulin','mq-a5a7f373bad71a5b-qa1','Insulin resistance is a condition in which the body produces insulin but does not use it effectively.', 'ineffective use despite production', 'negative', 'Does not mean complete absence of insulin'),
        ('prediabetes','INCREASES_RISK_OF','type2','mq-256baa3599c9abd2-qa0','If you have prediabetes, you are more likely to develop type 2 diabetes, heart disease, and stroke.', 'increased likelihood, not certainty', 'positive', 'Risk association, not inevitable progression'),
        ('prediabetes','INCREASES_RISK_OF','heart_disease','mq-256baa3599c9abd2-qa0','If you have prediabetes, you are more likely to develop type 2 diabetes, heart disease, and stroke.', 'increased likelihood', 'positive', 'Do not reverse the risk direction'),
        ('prediabetes','INCREASES_RISK_OF','stroke','mq-256baa3599c9abd2-qa0','If you have prediabetes, you are more likely to develop type 2 diabetes, heart disease, and stroke.', 'increased likelihood', 'positive', 'Do not claim all stroke causes diabetes'),
        ('obesity','INCREASES_RISK_OF','type2','mq-a586829366d7d100-qa0','You have a higher risk of type 2 diabetes if you are older, obese, have a family history of diabetes, or do not exercise.', 'type 2; population risk', 'positive', 'Not a personal probability or diagnosis'),
        ('family_history','INCREASES_RISK_OF','type2','mq-a586829366d7d100-qa0','You have a higher risk of type 2 diabetes if you are older, obese, have a family history of diabetes, or do not exercise.', 'type 2', 'positive', 'Risk factor, not certainty'),
        ('inactivity','INCREASES_RISK_OF','type2','mq-a586829366d7d100-qa0','You have a higher risk of type 2 diabetes if you are older, obese, have a family history of diabetes, or do not exercise.', 'type 2', 'positive', 'Not a causal inference from CDC features'),
        ('older_age','INCREASES_RISK_OF','type2','mq-a586829366d7d100-qa0','You have a higher risk of type 2 diabetes if you are older, obese, have a family history of diabetes, or do not exercise.', 'type 2; no threshold inferred', 'positive', 'No current screening age threshold asserted'),
        ('diabetes','MAY_DAMAGE','kidney_damage','mq-a0e5a1055ef417a6-qa0','If you have diabetes, your blood glucose, or blood sugar, levels are too high. Over time, this can damage your kidneys.', 'over time; hyperglycemia', 'positive', 'Diabetes to kidney damage; reverse relation unsupported by this quote'),
        ('kidney_damage','CHARACTERIZED_BY','early_asymptomatic','mq-39edc72b4c07d38d-qa3','People with diabetic kidney disease do not have symptoms in the early stages.', 'early stage', 'negative', 'Absence of early symptoms does not exclude kidney disease'),
        ('kidney_damage','HAS_SYMPTOM','edema','mq-39edc72b4c07d38d-qa3','edema', 'later progression; full parent context required', 'positive', 'A single word is anchored to the full reviewed QA; do not diagnose from edema'),
        ('activity','SUPPORTS','healthy_weight','mq-e4063412d94e5146-qa0','Starting a physical activity program can help you lose weight or keep a healthy weight and keep your blood glucose levels on target.', 'can help, not guarantee', 'positive', 'No universal exercise prescription'),
        ('activity','SUPPORTS','glucose','mq-e4063412d94e5146-qa0','Starting a physical activity program can help you lose weight or keep a healthy weight and keep your blood glucose levels on target.', 'glycemic management', 'positive', 'Supports target control, not cure'),
        ('healthy_eating','SUPPORTS','glucose','mq-caa9758d5a659141-qa0','Healthy eating helps keep your blood sugar in your target range.', 'individual target range', 'positive', 'No dose or universal meal quantities'),
        ('dietitian','SUPPORTS','meal_plan','mq-caa9758d5a659141-qa0','A registered dietitian can help make an eating plan just for you.', 'individualized planning', 'positive', 'Plan is individualized rather than a universal menu'),
        ('neuropathy','MAY_DAMAGE','foot_sensation','mq-b170342f78e4b1ad-qa0','Nerve damage from diabetes can cause you to lose feeling in your feet.', 'can cause sensory loss', 'positive', 'Source explicitly states nerve damage from diabetes'),
        ('diabetes','MAY_DAMAGE','foot_blood_supply','mq-b170342f78e4b1ad-qa0','Damage to the blood vessels can also mean that your feet do not get enough blood and oxygen.', 'diabetic foot parent context', 'positive', 'Read full QA; this edge is insufficient blood supply, not an assertion about all feet'),
        ('retinopathy','MAY_DAMAGE','retina','mq-411429effe32b2c4-qa0','Diabetic retinopathy damages the tiny blood vessels inside your retina.', 'retinal microvasculature', 'positive', 'Not the reverse direction'),
        ('gestational','INCREASES_RISK_OF','type2','mq-d042f10c8292d6dd-qa0','Most of the time, it goes away after you have your baby. But it does increase your risk for developing type 2 diabetes later on.', 'after gestational diabetes; later life', 'positive', 'It refers to gestational diabetes in full parent QA'),
        ('a1c','ASSESSES','glucose','mq-66c3595f48e5fa69-qa0','A blood test called the A1C can check to see how well you are managing your diabetes.', 'management monitoring', 'positive', 'Not a personal diagnosis from a model score'),
        ('type2','CHARACTERIZED_BY','insulin','mq-a586829366d7d100-qa0','With type 2 diabetes, the more common type, your body does not make or use insulin well.', 'production or utilization impairment', 'negative', 'Does not mean all type-2 patients produce zero insulin'),
    ]
    assertions = []
    for number,(sub,rel,obj,qa_id,quote,condition,polarity,note) in enumerate(specs,1):
        parent = parents[qa_id]
        if quote not in parent['answer']:
            raise ValueError(f'Quote mismatch in assertion {number}: {qa_id}')
        start = parent['answer'].index(quote)
        hits = [c['chunk_id'] for c in chunks if quote in c['content'] and any(r['qa_id']==qa_id for r in c['source_refs'])]
        if not hits:
            raise ValueError(f'No source chunk for assertion {number}')
        assertions.append({'id':f'kg2-a{number:03}', 'subject':sub,'relation':rel,'object':obj,
            'direction':'subject_to_object','polarity':polarity,'conditions':condition,
            'source_qa_id':qa_id,'document_id':parent['document_id'],'source_chunk_ids':hits,
            'quote':quote,'answer_start':start,'answer_end':start+len(quote),
            'source_url':parent['source_url'],'snapshot_url':parent['snapshot_url'],
            'review':{'status':'SOURCE_CHECKED_ASSISTANT','reviewer':'Codex assistant','date':'2026-11-02',
                      'not_clinical_expert_review':True,'direction_and_scope_note':note}})
    # Reject underspecified single-word evidence even if literal match passed.
    edema = next(a for a in assertions if a['object']=='edema')
    parent = parents[edema['source_qa_id']]
    answer = parent['answer']
    start = max(0, answer.rfind('. ',0,answer.index('edema'))+2)
    end = answer.find('. ',answer.index('edema'))
    quote = answer[start:end+1 if end>=0 else len(answer)].strip()
    assert len(quote)>40
    edema.update(quote=quote,answer_start=answer.index(quote),answer_end=answer.index(quote)+len(quote),
                 source_chunk_ids=[c['chunk_id'] for c in chunks if quote in c['content'] and any(r['qa_id']==edema['source_qa_id'] for r in c['source_refs'])])
    assert edema['source_chunk_ids']
    adjacency = defaultdict(list)
    for a in assertions:
        adjacency[a['subject']].append({'assertion_id':a['id'],'relation':a['relation'],'target':a['object']})
    used = {a['subject'] for a in assertions}|{a['object'] for a in assertions}
    payload = {'schema_version':'kg-seed-v1','construction':'manual assistant curation from full QA; no LLM extraction call',
               'source_corpus':'project01/datasets/llm_v2/chunks.jsonl','default_hops':1,'max_hops':2,
               'entities':entities,'relationships':assertions,
               'relation_allowlist':sorted({a['relation'] for a in assertions}),
               'limitations':['Historical MedQuAD snapshot, not current clinical guidance',
                             'Assistant review only; not clinical expert validation',
                             'Unconnected concepts are alias vocabulary for Phase 2; no unsupported medical edge',
                             'No missing-edge inference and no transitive causal inference',
                             'Provenance CONTAINS/MENTIONS and runtime lookup are built from ported notebook code in Phase 2']}
    dump(OUT/'seed_v1.json',payload)
    dump(OUT/'adjacency_seed_v1.json',dict(adjacency))
    stats={'entities':len(entities),'connected_entities':len(used),'alias_only_entities':len(entities)-len(used),
           'assertions':len(assertions),'source_qa_contexts':len({a['source_qa_id'] for a in assertions}),
           'source_documents':len({a['document_id'] for a in assertions}),
           'unique_source_chunks':len({c for a in assertions for c in a['source_chunk_ids']}),
           'reviewed_assertions':len(assertions),'automatic_extraction_calls':0,
           'runtime_graph_retrieval_implemented':False,'edge_count_is_not_confidence':True}
    dump(OUT/'seed_stats.json',stats)
    print(json.dumps(stats))


if __name__=='__main__':main()
