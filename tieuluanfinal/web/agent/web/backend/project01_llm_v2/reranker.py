# GENERATED from tieuluanfinal/notebooks/04_Multi_Agent.ipynb
from __future__ import annotations

import asyncio,json,re,logging,hashlib

from pathlib import Path

from types import SimpleNamespace

from typing import Any,Literal

from collections.abc import Sequence

from abc import ABC,abstractmethod

from .schemas import *

logger=logging.getLogger('project01_llm_v2.group');logger.addHandler(logging.NullHandler());logger.propagate=False

logger=logging.getLogger('project01_llm_v2.group');logger.addHandler(logging.NullHandler());logger.propagate=False

logger=logging.getLogger('project01_llm_v2.group');logger.addHandler(logging.NullHandler());logger.propagate=False

settings=SimpleNamespace(bm25_store_path='unused-explicit-store-required',rerank_top_k=20,rerank_top_n=6,default_chunk_size=1600,default_chunk_overlap=160)

class BaseReranker(ABC):
    """Interface chung cho các reranker."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_n: int | None = None,
    ) -> list[RankedResult]:
        """Sắp xếp lại kết quả retrieval theo độ liên quan."""
        ...

    @staticmethod
    def _to_ranked_result(
        result: SearchResult,
        rerank_score: float,
        original_rank: int,
    ) -> RankedResult:
        return RankedResult(
            **result.model_dump(),
            rerank_score=rerank_score,
            original_rank=original_rank,
        )

class LocalEvidenceReranker(BaseReranker):
    """Lightweight local reranker following the reference BGEReranker interface.

    It combines the already computed hybrid RRF score with lexical coverage and
    the source-checked KG contribution. It never calls an LLM or external API.
    BGE CrossEncoder is intentionally not loaded in the small Render/serving env.
    """
    provider='local_weighted_rrf_lexical_kg'
    api_calls=0

    def __init__(self):
        self.usage=[]
        self.last_report={'provider':self.provider,'api_calls':0,'candidate_count':0,'scored_count':0,'evidence_count':0,'threshold':None,'top_n':6,'ranking':[]}

    @staticmethod
    def _terms(text):
        stop={'a','an','and','are','as','at','be','by','for','from','how','in','is','it','of','on','or','the','to','what','with',
              'bị','có','của','cho','do','không','là','làm','nguy','nào','như','tăng','thế','thì','và','với'}
        return {term for term in re.findall(r'(?u)\b\w{2,}\b',text.casefold()) if term not in stop}

    async def rerank(self,query,results,top_n=6):
        if not results:return []
        limit=min(top_n,len(results));query_terms=self._terms(query);max_rrf=max((r.score for r in results),default=1.0) or 1.0
        scored=[]
        for original_rank,result in enumerate(results,1):
            content_terms=self._terms(result.content);title_terms=self._terms(result.metadata.title or '')
            denominator=max(1,len(query_terms))
            lexical=0.7*len(query_terms & content_terms)/denominator+0.3*len(query_terms & title_terms)/denominator
            retrieval=max(0.0,min(1.0,result.score/max_rrf));kg=1.0/result.kg_rank if result.kg_rank else 0.0
            score=round(0.55*retrieval+0.35*lexical+0.10*kg,8)
            scored.append(self._to_ranked_result(result,score,original_rank))
        scored.sort(key=lambda row:(-row.rerank_score,row.original_rank,row.chunk_id));kept=scored[:limit]
        kept_ids={row.chunk_id for row in kept};model_rank={row.chunk_id:i for i,row in enumerate(scored,1)}
        by_id={row.chunk_id:row for row in scored}
        self.last_report={'provider':self.provider,'api_calls':0,'candidate_count':len(results),'scored_count':len(scored),'evidence_count':len(kept),'threshold':None,'top_n':limit,
            'weights':{'hybrid_rrf':0.55,'lexical_coverage':0.35,'kg_source_boost':0.10},
            'ranking':[{'chunk_id':r.chunk_id,'title':r.metadata.title,'input_rank':i,'model_rank':model_rank[r.chunk_id],
                        'rerank_score':by_id[r.chunk_id].rerank_score,'selected':r.chunk_id in kept_ids,
                        'reason':'selected' if r.chunk_id in kept_ids else 'over_top_n'} for i,r in enumerate(results,1)]}
        return kept

