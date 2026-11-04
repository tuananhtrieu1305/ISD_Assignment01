# GENERATED from notebooks/02_Diabetes_Multi_Agent.ipynb; source SHA256 d44a09c22107c88ed5559733052ed5d401373495201821d1748cf1e86badd436
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

from .reranker import BaseReranker

from .query import StrategyName

class ChatbotPipeline:
    """Điều phối toàn bộ luồng RAG của chatbot."""

    def __init__(self,generator,retriever,reranker):
            self.generator=generator;self.retriever=retriever;self.reranker=reranker;self.retrieved_results=[];self.final_results=[]

    async def ask(
        self,
        question: str,
        *,
        use_pre_retrieval: bool = True,
        strategy: StrategyName = "expansion",
        use_rerank: bool = True,
        retrieval_top_k: int | None = None,
        rerank_top_n: int | None = None,
    ) -> ChatResponse:
        """Trả lời câu hỏi bằng retrieval, rerank và generation."""
        try:
            retrieved_results = await self.retriever.retrieve(
                question,
                use_pre_retrieval=use_pre_retrieval,
                strategy=strategy,
                top_k=retrieval_top_k,
            )

            final_results: Sequence[SearchResult] = retrieved_results
            if use_rerank:
                logger.info(
                    "RERANK | enabled=true | provider=%s | query=%r | "
                    "input_count=%d | requested_top_n=%s",
                    self.reranker.__class__.__name__,
                    question,
                    len(retrieved_results),
                    rerank_top_n if rerank_top_n is not None else "default",
                )
                self._log_ranked_results("RERANK BEFORE", retrieved_results)
                final_results = await self.reranker.rerank(
                    question,
                    retrieved_results,
                    top_n=rerank_top_n,
                )
                self._log_ranked_results("RERANK AFTER", final_results)
            else:
                logger.info(
                    "RERANK | enabled=false | query=%r | input_count=%d | "
                    "retrieval_order_retained=true",
                    question,
                    len(retrieved_results),
                )
                self._log_ranked_results(
                    "RERANK OUTPUT (disabled)",
                    retrieved_results,
                )

            self.retrieved_results=list(retrieved_results);self.final_results=list(final_results)
            answer = await self.generator.generate(question, final_results)
            response = ChatResponse(
                answer=answer,
                sources=self._build_sources(final_results),
            )
            logger.info(
                "Pipeline đã xử lý câu hỏi với %d nguồn",
                len(response.sources),
            )
            return response
        except Exception:
            logger.exception("Lỗi khi xử lý câu hỏi trong pipeline")
            raise

    @staticmethod
    def _log_ranked_results(
        stage: str,
        results: Sequence[SearchResult],
    ) -> None:
        """Log thứ tự, điểm và nội dung rút gọn để so sánh reranking."""
        if not results:
            logger.info("%s | result_count=0", stage)
            return

        for position, result in enumerate(results, start=1):
            metadata = result.metadata
            preview = " ".join(result.content.split())
            if len(preview) > 180:
                preview = f"{preview[:177]}..."

            if isinstance(result, RankedResult):
                logger.info(
                    "%s [%02d] | chunk_id=%s | title=%r | dieu=%r | "
                    "retrieval_score=%.6f | rerank_score=%.6f | "
                    "original_rank=%d | preview=%r",
                    stage,
                    position,
                    result.chunk_id,
                    metadata.title,
                    metadata.section,
                    result.score,
                    result.rerank_score,
                    result.original_rank,
                    preview,
                )
            else:
                logger.info(
                    "%s [%02d] | chunk_id=%s | title=%r | dieu=%r | "
                    "retrieval_score=%.6f | preview=%r",
                    stage,
                    position,
                    result.chunk_id,
                    metadata.title,
                    metadata.section,
                    result.score,
                    preview,
                )

    @staticmethod
    def _build_sources(
        results: Sequence[SearchResult],
    ) -> list[SourceResponse]:
        return [
            SourceResponse(
                chunk_id=result.chunk_id,
                content=result.content,
                chunk_index=result.chunk_index,
                metadata=result.metadata,
                score=(
                    result.rerank_score
                    if isinstance(result, RankedResult)
                    else result.score
                ),
                score_type=("rerank" if isinstance(result, RankedResult) else "rrf"),
            )
            for result in results
        ]

