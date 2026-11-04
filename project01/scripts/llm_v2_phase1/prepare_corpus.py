"""Source preparation only; preserve sentence/QA offsets for later notebook retrieval."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re

PROJECT=Path(__file__).resolve().parents[2];DATA=PROJECT/'datasets/llm_v2'
def sha(text):return hashlib.sha256(text.encode()).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def lines(path):return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]

def main():
    output=DATA/'chunks.jsonl'
    if output.exists():raise RuntimeError('Prepared corpus exists; use a revision')
    selected=[];excluded=[]
    for doc in lines(DATA/'documents.jsonl'):
        family=doc['source_xml_path'].split('/')[0]
        keep=family.startswith(('4_','5_','6_','7_','8_')) and 'insipidus' not in doc['title'].lower() and 'Financial Help' not in doc['title']
        (selected if keep else excluded).append(doc)
    chunks={};parents=[]
    for doc in selected:
        for ordinal,pair in enumerate(doc['qa_pairs']):
            parent_id=doc['document_id']+'-qa'+str(ordinal)
            parent={**pair,'qa_id':parent_id,'original_qa_id':pair['qa_id'],'document_id':doc['document_id'],'title':doc['title'],'source_url':doc['source_url'],'snapshot_url':doc['snapshot_url']}
            parents.append(parent);answer=pair['answer']
            boundaries=[0]+[m.end() for m in re.finditer(r'(?<=[.!?])\s+(?=[A-Z0-9])',answer)]+[len(answer)]
            start_index=0
            while start_index<len(boundaries)-1:
                end_index=start_index+1
                while end_index<len(boundaries)-1 and boundaries[end_index+1]-boundaries[start_index]<=1600:end_index+=1
                start=boundaries[start_index];end=boundaries[end_index]
                content=answer[start:end].strip();start=answer.find(content,start)
                if content:
                    key='m2c-'+sha(content)[:20]
                    ref={'document_id':doc['document_id'],'qa_id':parent_id,'answer_start':start,'answer_end':start+len(content),'source_url':doc['source_url'],'snapshot_url':doc['snapshot_url']}
                    if key in chunks:chunks[key]['source_refs'].append(ref)
                    else:chunks[key]={'chunk_id':key,'content':content,'text_sha256':sha(content),'title':doc['title'],'section':pair['question'],'language':'en','source_refs':[ref]}
                if end_index>=len(boundaries)-1:break
                start_index=max(start_index+1,end_index-1)
    ordered=sorted(chunks.values(),key=lambda row:row['chunk_id'])
    output.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in ordered),encoding='utf-8')
    (DATA/'qa_context.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in parents),encoding='utf-8')
    (DATA/'corpus_documents.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in selected),encoding='utf-8')
    dump(DATA/'selection.json',{'selection':'NIH general diabetes mellitus sources 4/5/6/7/8, exclude diabetes insipidus and financial-help-only document; no retrieval scores used','included':[{k:doc[k] for k in ['document_id','title','source_xml_path']} for doc in selected],'excluded':[{k:doc[k] for k in ['document_id','title','source_xml_path']} for doc in excluded]})
    stats={'documents':len(selected),'qa_contexts':len(parents),'unique_chunks':len(ordered),'source_references':sum(len(r['source_refs']) for r in ordered),
      'characters':{'min':min(len(r['content']) for r in ordered),'max':max(len(r['content']) for r in ordered),'mean':sum(len(r['content']) for r in ordered)/len(ordered)},
      'document_distribution':dict(Counter(doc['source_xml_path'].split('/')[0] for doc in selected)),
      'chunk_policy':'Soft 1600 character target, complete sentence boundaries, one sentence overlap, long sentence retained, exact QA answer offsets; duplicate chunk text merged with all source refs',
      'original_urls':sum(bool(doc['source_url']) for doc in selected),'language':'en','old_corpus_unchanged':True,'fit_or_model_evaluation':False}
    dump(DATA/'corpus_stats.json',stats)
    (DATA/'ATTRIBUTION.md').write_text('# MedQuAD diabetes mellitus subset v2\n\nDerived from MedQuAD commit 577bd37b96c02d1833b2c9eed2de9f96964e96cb, https://github.com/abachaa/MedQuAD . Dataset CC BY 4.0; preserve raw/MedQuAD_LICENSE.txt and individual original website terms. Source URLs are recovered from XML attributes, not invented. Transformations: general-domain diabetes selection, full QA normalization, sentence-aware chunks and exact-text deduplication; old corpus unchanged. Snapshot is historical, not certified current medical guidance.\n',encoding='utf-8')
    print(json.dumps(stats))

if __name__=='__main__':main()
