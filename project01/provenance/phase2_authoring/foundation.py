"""Medical-only immutable assets, frozen MLP inference and query-driven KB/KG retrieval."""
from pathlib import Path
import hashlib
import json
import math
import re
import sys
import types
import unicodedata

import joblib
import numpy as np
from sklearn.preprocessing import normalize

STOPWORDS = {'a','an','and','are','as','at','be','by','did','do','does','for','from','how','in','is','it','of','on','or','that','the','their','this','to','was','were','what','when','where','which','who','why','with','would'}
SOURCE_URL='https://github.com/abachaa/MedQuAD/tree/577bd37b96c02d1833b2c9eed2de9f96964e96cb'
LIMITATION='Học thuật trên snapshot; score nhãn khảo sát, không phải chẩn đoán hoặc xác suất mắc mới. Trích đoạn gốc tiếng Anh.'

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def file_sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def tokenize(text):
    """Exact analyzer used by the preserved BM25/LSA indexes."""
    return [word for word in re.findall(r'[a-z0-9]+',str(text).casefold()) if word not in STOPWORDS]

def stable_ranking(ids,scores,top_k,positive_only=False):
    scores=np.asarray(scores,dtype=np.float64).reshape(-1)
    selected=np.flatnonzero(scores>0) if positive_only else np.arange(len(ids))
    ordered=selected[np.lexsort((np.asarray(ids,dtype=str)[selected],-scores[selected]))]
    return [(str(ids[i]),float(scores[i])) for i in ordered[:top_k]]

class BM25Index:
    """Inference methods for the existing trusted serialized index; no fitting."""
    def search(self,query,top_k=10):
        terms=self.vectorizer.transform([query]).indices
        if not terms.size:return []
        scores=np.zeros(len(self.doc_ids),dtype=np.float32)
        norm=self.k1*(1-self.b+self.b*self.doc_lengths/max(self.average_doc_length,1e-8))
        for term in terms:
            start,end=self.counts_csc.indptr[term],self.counts_csc.indptr[term+1]
            rows=self.counts_csc.indices[start:end];frequencies=self.counts_csc.data[start:end]
            scores[rows]+=self.idf[term]*(frequencies*(self.k1+1))/(frequencies+norm[rows])
        return stable_ranking(self.doc_ids,scores,top_k,True)

class DenseLSAIndex:
    """TF-IDF/SVD index query, not a neural embedding model."""
    def search(self,query,top_k=10):return self.search_batch([query],top_k,1)[0]
    def search_batch(self,queries,top_k=10,batch_size=32):
        output=[]
        for start in range(0,len(queries),batch_size):
            batch=queries[start:start+batch_size]
            counts=self.vectorizer.transform(batch)
            vectors=normalize(self.svd.transform(self.tfidf.transform(counts)).astype(np.float32),norm='l2',copy=False)
            scores=vectors@self.vectors.T
            for i in range(len(batch)):
                output.append([] if counts[i].nnz==0 else stable_ranking(self.doc_ids,scores[i],top_k))
        return output

def install_index_compatibility():
    """Resolve old pickle names to code defined in this notebook/export, not old .py."""
    for name in ['term_paper','term_paper.tools','term_paper.tools.phase14_rag']:
        module=types.ModuleType(name);module.__path__=[];sys.modules[name]=module
        parent,_,child=name.rpartition('.')
        if parent:setattr(sys.modules[parent],child,module)
    module=sys.modules['term_paper.tools.phase14_rag']
    module.BM25Index=BM25Index;module.DenseLSAIndex=DenseLSAIndex;module.tokenize=tokenize

def plain(text):
    text=unicodedata.normalize('NFKD',text.casefold()).replace('đ','d')
    return re.sub(r'\s+',' ',''.join(c for c in text if not unicodedata.combining(c))).strip()

def validate_profile(profile,schema):
    if not isinstance(profile,dict):return {'valid':False,'missing':schema['required'],'invalid':[],'extra':[]}
    missing=[k for k in schema['required'] if k not in profile or profile[k] is None]
    invalid=[]
    for name,value in profile.items():
        if name not in schema['limits']:continue
        bounds=schema['limits'][name]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not bounds[0]<=value<=bounds[1] or (name!='bmi' and value!=int(value)):
            invalid.append(name)
    extra=sorted(set(profile)-set(schema['required']))
    return {'valid':not(missing or invalid or extra),'missing':missing,'invalid':invalid,'extra':extra}

def transform_profile(profile,preprocessing):
    """Apply frozen train-only numeric statistics in canonical input order."""
    values=[]
    for name in preprocessing['input_columns']:
        rule=preprocessing['numeric'][name]
        values.append((float(profile[name])-rule['mean'])/rule['std'])
    return np.asarray([values],dtype=np.float32)

def mlp_forward(tensor,plan,weights):
    tensor=np.asarray(tensor,dtype=next(iter(weights.values())).dtype)
    if tensor.shape!=(1,21) or not np.isfinite(tensor).all():raise ValueError('Invalid model tensor')
    for step in plan['steps']:
        if step['kind']=='dense':tensor=tensor@weights[step['id']+'/w']+weights[step['id']+'/b']
        elif step['kind']=='activation':tensor=np.maximum(tensor,0)
        else:raise ValueError('Only frozen MLP plan supported')
    return float(tensor[0,0])

def probability(logit):return float(1/(1+np.exp(-np.clip(logit,-60,60))))

def normalize_query(question,language,glossary):
    mapping=[]
    if language=='vi':
        normalized=plain(question);terms=[]
        for source,target in sorted(glossary.items(),key=lambda p:-len(p[0])):
            if re.search(r'\b'+re.escape(plain(source))+r'\b',normalized):
                mapping.append({'from':source,'to':target});terms.extend(tokenize(target))
        terms.extend(re.findall(r'\b(?:insulin|a1c|bmi|cholesterol|glucose|neuropathy|retinopathy)\b',normalized))
    else:
        text=question.split(' Also report')[0]
        scaffolding={'explain','preserved','evidence','about','snapshot','document','report','say','says','also','model','score','supplied','survey','profile','structured','fields','attached','checkpoint','output','calculate','binary','historical','using','sourced','explanation'}
        terms=[t for t in tokenize(text) if t not in scaffolding]
    return ' '.join(dict.fromkeys(terms)),mapping

def focus_terms(query):
    return set(tokenize(query))-{'diabetes','diabetic','mellitus','type','1','2'}

def graph_candidates(query,graph):
    normalized=plain(query);terms=set(normalized.split());matched=[]
    for key,node in graph.items():
        if key and (key in normalized or (len(key.split())>1 and set(key.split())<=terms)):matched.append((key,node))
    matched.sort(key=lambda item:(-len(item[0]),item[0]));paths={}
    for _,node in matched[:4]:
        for chunk_id in node['chunk_ids']:paths.setdefault(chunk_id,[node['node_id'],chunk_id])
    return paths

def fuse_rankings(sparse,dense,paths,settings):
    graph=[pair for pair in sparse if pair[0] in paths]
    seen={key for key,_ in graph}
    graph.extend((key,0.0) for key in sorted(set(paths)-seen))
    scores={}
    for name,ranking in [('sparse',sparse),('dense',dense),('graph',graph[:100])]:
        for rank,(key,_) in enumerate(ranking,start=1):scores[key]=scores.get(key,0)+settings['weights'][name]/(settings['rrf_k']+rank)
    return sorted(scores.items(),key=lambda pair:(-pair[1],pair[0]))[:settings['top_k']]

def supported_excerpt(query,evidence):
    """Extract a focused source span; lexical support is a heuristic, reviewed later."""
    focus=focus_terms(query);candidates=[]
    for rank,row in enumerate(evidence):
        sentences=re.split(r'(?<=[.!?])\s+|\s+-\s+',row['text'])
        for sentence in sentences:
            sentence=sentence.strip()
            overlap=focus&set(tokenize(sentence))
            if len(sentence)>=25 and (not focus or len(overlap)>=max(1,math.ceil(len(focus)*0.5))):
                span=sentence[:420]
                if len(sentence)>420:span=span.rsplit(' ',1)[0]
                candidates.append((len(overlap),-rank,-len(span),span,row))
    if not candidates:return {'answer':'','citations':[],'support_kind':'insufficient'}
    _,_,_,answer,row=max(candidates,key=lambda value:value[:3])
    return {'answer':answer,'citations':[row['chunk_id']],'support_kind':'verbatim_focused_excerpt_heuristic'}

class Runtime:
    def __init__(self,package):
        self.package=Path(package).resolve();self.manifest=read_json(self.package/'manifest.json')
        for row in self.manifest['files']:
            path=(self.package/row['path']).resolve()
            if not path.is_relative_to(self.package) or file_sha(path)!=row['sha256']:raise ValueError('Package integrity error')
        self.schema=read_json(self.package/'profile_schema.json')
        self.preprocessing=read_json(self.package/'preprocessing.json')
        self.config=read_json(self.package/'model_config.json')
        self.glossary=read_json(self.package/'query_glossary.json')['mapping']
        self.settings=read_json(self.package/'retrieval.json')
        self.chunks={row['chunk_id']:row for row in (json.loads(line) for line in (self.package/'medical_chunks.jsonl').read_text().splitlines())}
        self.graph=read_json(self.package/'medical_graph.json')
        install_index_compatibility()
        self.sparse=joblib.load(self.package/'kg_medical_bm25.joblib')
        self.dense=joblib.load(self.package/'kg_medical_dense_lsa.joblib')
        with np.load(self.package/'model.npz',allow_pickle=False) as archive:self.weights={name:archive[name].copy() for name in archive.files}
        if set(self.sparse.doc_ids)!=set(self.chunks) or set(self.dense.doc_ids)!=set(self.chunks):raise ValueError('Index/corpus mismatch')
        if any(not set(node['chunk_ids'])<=set(self.chunks) for node in self.graph.values()):raise ValueError('Graph reference mismatch')
        if self.preprocessing['input_columns']!=self.schema['feature_order']:raise ValueError('Feature order mismatch')
        self.model_hash=file_sha(self.package/'model.npz')

    def predict(self,profile):
        validation=validate_profile(profile,self.schema)
        if not validation['valid']:raise ValueError('Incomplete/invalid profile')
        logit=mlp_forward(transform_profile(profile,self.preprocessing),self.config['plan'],self.weights)
        score=probability(logit)
        return {'score':score,'class_id':int(score>0.5),'class_name':self.schema['class_names'][str(int(score>0.5))],'logit':logit,'model_sha256':self.model_hash,'profile_sha256':digest(profile),'unit':'historical_binary_model_score','calibrated_incidence_risk':False}

    def retrieve(self,question,language='en',expanded=False):
        query,mapping=normalize_query(question,language,self.glossary)
        if expanded:
            expansions={'kidney':'renal','heart':'cardiovascular','foot':'feet','blood pressure':'hypertension'}
            for source,target in expansions.items():
                if source in query:query+=' '+target
        sparse=self.sparse.search(query,100);dense=self.dense.search(query,100)
        paths=graph_candidates(query,self.graph)
        ranking=fuse_rankings(sparse,dense,paths,self.settings)
        evidence=[]
        for key,score in ranking:
            row=self.chunks[key]
            evidence.append({**row,'score':score,'source_url':SOURCE_URL,'locator':row['document_id']+'/'+key,'text_sha256':hashlib.sha256(row['text'].encode()).hexdigest(),'source_sha256':self.manifest['source_corpus_sha256'],'graph_path':paths.get(key,[])})
        draft=supported_excerpt(query,evidence)
        return {'query_original':question,'query_normalized':query,'mapping':mapping,'expanded':expanded,'ranked_chunk_ids':[key for key,_ in ranking],'evidence':evidence,'graph_paths':paths,**draft,'language':'en','method':'BM25 + LSA + lexical graph / weighted RRF','citation_scope':'source repository commit plus local document/chunk, not original page URL'}
