# GENERATED from notebooks/01_Data_KB_RAG.ipynb; source SHA256 609195cb2f081a9e9aaade7a6ebc5c7205e2f9a9e95f1f33a126f5d62363afbe
# Edit notebook cells; export with scripts/llm_v2_phase2/notebooks.py export.
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

from .query import PreRetriever,StrategyName

class HybridSearcher:
    """Kết hợp dense search và BM25 bằng Reciprocal Rank Fusion."""

    def __init__(self,embedder,vector_db,bm25_store,graph=None,dense_weight=.4,sparse_weight=.4,rrf_k=60):
            self.embedder=embedder;self.vector_db=vector_db;self.bm25_store=bm25_store;self.graph=graph
            self.dense_weight=dense_weight;self.sparse_weight=sparse_weight;self.rrf_k=rrf_k;self.entity_ids=[]

    async def search(self,query,top_k=None):
            result_count=top_k or 20
            dense_results=await self._dense_search(query,result_count)
            sparse_results=await self._sparse_search(query,result_count)
            kg_results=self.graph.search(query,self.entity_ids) if self.graph else []
            return self._fuse(dense_results,sparse_results,top_k=result_count,kg_results=kg_results)

    async def _dense_search(
        self,
        query: str,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Tạo query embedding và tìm kiếm vector trên Qdrant."""
        try:
            query_vector = await self.embedder.embed_text(query)
            results = await self.vector_db.query(query_vector, top_k=top_k)
            logger.debug("Dense search trả về %d kết quả", len(results))
            return results
        except Exception:
            logger.exception("Lỗi tại nhánh dense search trên Qdrant")
            raise

    async def _sparse_search(
        self,
        query: str,
        top_k: int,
    ) -> list[dict[str, object]]:
        """Tìm kiếm từ khóa trên BM25."""
        try:
            results = await self.bm25_store.search(query, top_k=top_k)
            logger.debug("Sparse search trả về %d kết quả", len(results))
            return results
        except Exception:
            logger.exception("Lỗi tại nhánh sparse search bằng BM25")
            raise

    def _fuse(
        self,
        dense_results: list[dict[str, Any]],
        sparse_results: list[dict[str, object]],
        *,
        top_k: int,
        kg_results=None,
    ) -> list[SearchResult]:
        merged: dict[str, dict[str, Any]] = {}

        for rank, result in enumerate(dense_results, start=1):
            chunk_id = str(result["id"])
            merged[chunk_id] = {
                "payload": result["payload"],
                "score": self.dense_weight / (self.rrf_k + rank),
                "dense_rank": rank,
                "sparse_rank": None,
            }

        for rank, result in enumerate(sparse_results, start=1):
            chunk_id = str(result["id"])
            rrf_score = self.sparse_weight / (self.rrf_k + rank)

            if chunk_id in merged:
                merged[chunk_id]["score"] += rrf_score
                merged[chunk_id]["sparse_rank"] = rank
            else:
                merged[chunk_id] = {
                    "payload": result["payload"],
                    "score": rrf_score,
                    "dense_rank": None,
                    "sparse_rank": rank,
                }

        for rank,result in enumerate(kg_results or [],start=1):
            cid=result['id']
            if cid not in merged:merged[cid]={'payload':result['payload'],'score':0.,'dense_rank':None,'sparse_rank':None}
            merged[cid]['score']+=.2/(self.rrf_k+rank)
            merged[cid]['kg_rank']=rank;merged[cid]['graph_assertion_ids']=result['assertion_ids']

        ranked_items = sorted(
            merged.items(),
            key=lambda item: item[1]["score"],
            reverse=True,
        )[:top_k]

        return [
            self._to_search_result(chunk_id, data)
            for chunk_id, data in ranked_items
        ]

    @staticmethod
    def _to_search_result(
        chunk_id: str,
        data: dict[str, Any],
    ) -> SearchResult:
        payload = data["payload"]
        return SearchResult(
            chunk_id=chunk_id,
            content=payload["content"],
            chunk_index=payload["chunk_index"],
            metadata=MetaData.model_validate(payload["metadata"]),
            score=data["score"],
            dense_rank=data["dense_rank"],
            sparse_rank=data["sparse_rank"],
            kg_rank=data.get("kg_rank"),
            graph_assertion_ids=data.get("graph_assertion_ids",[]),
        )

class Retriever:
    """Điều phối pre-retrieval và hybrid search."""

    def __init__(self,hybrid_searcher,pre_retriever=None):
            self.hybrid_searcher=hybrid_searcher;self.pre_retriever=pre_retriever

    async def retrieve(self,query,*,use_pre_retrieval=True,strategy='rewrite',top_k=20):
            queries=await self._prepare_queries(query,use_pre_retrieval,strategy)
            if self.pre_retriever:self.hybrid_searcher.entity_ids=self.pre_retriever.plan.get('entity_ids',[])
            result_groups=[]
            for item in queries[:3]:result_groups.append(await self.hybrid_searcher.search(item,top_k=top_k))
            return self._merge_results(result_groups,top_k)

    async def _prepare_queries(
        self,
        query: str,
        use_pre_retrieval: bool,
        strategy: StrategyName,
    ) -> list[str]:
        if not use_pre_retrieval:
            logger.info(
                "PRE-RETRIEVAL | enabled=false | strategy=%s (ignored) | "
                "original_query=%r | output_count=1",
                strategy,
                query,
            )
            logger.info(
                "PRE-RETRIEVAL OUTPUT [01] | strategy=disabled | query=%r",
                query,
            )
            return [query]
        if self.pre_retriever is None:
            raise RuntimeError("PreRetriever chưa được khởi tạo")
        return await self.pre_retriever.process(query, strategy)

    @staticmethod
    def _merge_results(
        result_groups: list[list[SearchResult]],
        top_k: int,
    ) -> list[SearchResult]:
        best_results: dict[str, SearchResult] = {}

        for results in result_groups:
            for result in results:
                current = best_results.get(result.chunk_id)
                if current is None or result.score > current.score:
                    best_results[result.chunk_id] = result

        return sorted(
            best_results.values(),
            key=lambda result: result.score,
            reverse=True,
        )[:top_k]

