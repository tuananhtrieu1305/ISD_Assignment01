# GENERATED from notebooks/01_Data_KB_RAG.ipynb; source SHA256 609195cb2f081a9e9aaade7a6ebc5c7205e2f9a9e95f1f33a126f5d62363afbe
# Edit notebook cells; export with scripts/llm_v2_phase2/notebooks.py export.
"""Group Embedder/VectorDBClient interfaces adapted to Gemini and local NumPy."""

from pathlib import Path

import json

import numpy as np

from .provider import atomic_json,digest,read_json

from .schemas import Chunk,MetaData

class Embedder:
    def __init__(self,gateway,batch_size=8):self.gateway=gateway;self.batch_size=batch_size

    @staticmethod
    def normalize(vector):
        value=np.asarray(vector,dtype=np.float32)
        if value.shape!=(768,) or not np.isfinite(value).all() or np.linalg.norm(value)==0:raise ValueError('Invalid embedding vector')
        return (value/np.linalg.norm(value)).tolist()

    async def embed_text(self,text):
        response=await self.gateway.embed(text,'RETRIEVAL_QUERY')
        if len(response['vectors'])!=1:raise ValueError('Embedding count mismatch')
        return self.normalize(response['vectors'][0])

    async def embed_batch(self,texts):
        response=await self.gateway.embed(list(texts),'RETRIEVAL_DOCUMENT')
        if len(response['vectors'])!=len(texts):raise ValueError('Embedding count mismatch')
        return [self.normalize(vector) for vector in response['vectors']]

class VectorDBClient:
    def __init__(self,path):
        self.path=Path(path);self.points=read_json(self.path) if self.path.exists() else []

    async def upsert(self,points):
        current={p['id']:p for p in self.points};current.update({p['id']:p for p in points});self.points=list(current.values());atomic_json(self.path,self.points)

    async def query(self,query_vector,top_k=20):
        if not self.points:return []
        matrix=np.asarray([p['vector'] for p in self.points],dtype=np.float32)
        scores=matrix@np.asarray(query_vector,dtype=np.float32)
        return [{**self.points[i],'score':float(scores[i])} for i in np.argsort(-scores,kind='stable')[:top_k]]

    async def check_exists(self,document_id):
        return any(p['payload']['metadata']['document_id']==document_id for p in self.points)

def load_corpus(root):
    rows=[json.loads(line) for line in (Path(root)/'datasets/llm_v2/chunks.jsonl').read_text(encoding='utf-8').splitlines()]
    return [Chunk(chunk_id=r['chunk_id'],content=r['content'],chunk_index=i,
                  metadata=MetaData(document_id=r['source_refs'][0]['document_id'],title=r['title'],
                    source=r['source_refs'][0]['source_url'],section=r['section'],source_refs=r['source_refs'])) for i,r in enumerate(rows)]

def index_fingerprint(chunks):
    return digest({'chunks':[r.model_dump() for r in chunks],'model':'gemini-embedding-001','dimensions':768,
                   'task':'RETRIEVAL_DOCUMENT','normalization':'L2','version':'medical-index-v1'})

