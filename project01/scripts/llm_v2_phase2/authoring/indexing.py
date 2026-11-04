from __future__ import annotations
import asyncio,json,re,logging,hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any,Literal
from collections.abc import Sequence
from abc import ABC,abstractmethod
from .schemas import *
logger=logging.getLogger('project01_llm_v2.group');logger.addHandler(logging.NullHandler());logger.propagate=False
settings=SimpleNamespace(bm25_store_path='unused-explicit-store-required',rerank_top_k=20,rerank_top_n=6,default_chunk_size=1600,default_chunk_overlap=160)
from langchain_text_splitters import MarkdownHeaderTextSplitter,RecursiveCharacterTextSplitter
class DocumentChunker:
    """Create chunks after splitting Markdown by chapter, section and article."""

    HEADERS_TO_SPLIT_ON = [
        ("#", "title"),
        ("##", "section"),
        ("###", "subsection"),
    ]
    SEPARATORS = ["\n\n", "\n", ". ", "; ", ", ", " ", ""]

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self.chunk_size = (
            settings.default_chunk_size if chunk_size is None else chunk_size
        )
        self.chunk_overlap = (
            settings.default_chunk_overlap
            if chunk_overlap is None
            else chunk_overlap
        )
        self._validate_chunk_config()

        self._header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.HEADERS_TO_SPLIT_ON,
            strip_headers=False,
        )
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.SEPARATORS,
            length_function=len,
        )

    def split_markdown(
        self,
        markdown_text: str,
        *,
        document_id: str,
        title: str,
        source: str | None = None,
    ) -> list[Chunk]:
        """Split Markdown hierarchy first, then split each section into chunks."""
        if not markdown_text.strip():
            raise ValueError("Markdown content must not be empty")
        if not document_id.strip():
            raise ValueError("document_id must not be empty")
        if not title.strip():
            raise ValueError("title must not be empty")

        sections = self._header_splitter.split_text(markdown_text)
        documents = self._text_splitter.split_documents(sections)
        chunks: list[Chunk] = []

        for chunk_index, document in enumerate(documents):
            content = document.page_content.strip()
            if not content:
                continue

            metadata = MetaData(
                document_id=document_id,
                title=title,
                source=source,
                section=document.metadata.get("section"),
                subsection=document.metadata.get("subsection"),
            )
            chunk_id = "m2c-"+hashlib.sha256(content.encode()).hexdigest()[:20]
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    content=content,
                    chunk_index=chunk_index,
                    metadata=metadata,
                )
            )

        logger.info("Created %d chunks from document %s", len(chunks), document_id)
        return chunks

    def split_file(
        self,
        file_path: str | Path,
        *,
        document_id: str | None = None,
        title: str | None = None,
    ) -> list[Chunk]:
        """Read and split one UTF-8 Markdown file."""
        path = Path(file_path)
        if path.suffix.lower() != ".md":
            raise ValueError(f"Only Markdown files are supported: {path}")
        if not path.is_file():
            raise FileNotFoundError(f"Markdown file not found: {path}")

        markdown_text = path.read_text(encoding="utf-8")
        return self.split_markdown(
            markdown_text,
            document_id=document_id or path.stem,
            title=title or path.stem.replace("-", " ").replace("_", " "),
            source=str(path),
        )

    async def asplit_file(
        self,
        file_path: str | Path,
        *,
        document_id: str | None = None,
        title: str | None = None,
    ) -> list[Chunk]:
        """Run file reading and chunking without blocking the event loop."""
        return await asyncio.to_thread(
            self.split_file,
            file_path,
            document_id=document_id,
            title=title,
        )

    def _validate_chunk_config(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

class DocumentIndexer:
    """Điều phối chunking, embedding, Qdrant và BM25 indexing."""

    def __init__(self,chunker,embedder,vector_db,bm25_store):
            self.chunker=chunker;self.embedder=embedder;self.vector_db=vector_db;self.bm25_store=bm25_store;self._index_lock=asyncio.Lock()

    async def index_file(
        self,
        file_path: str | Path,
        *,
        document_id: str | None = None,
        title: str | None = None,
    ) -> dict[str, object]:
        """Index một file Markdown vào cả Qdrant và BM25."""
        path = Path(file_path)
        resolved_document_id = (document_id or path.stem)+":"+hashlib.sha256(path.read_bytes()).hexdigest()[:16]

        async with self._index_lock:
            try:
                if not path.is_file():
                    raise FileNotFoundError(f"Không tìm thấy tài liệu: {path}")
                if path.suffix.lower() != ".md":
                    raise ValueError(f"Chỉ hỗ trợ file Markdown: {path}")

                dense_exists, bm25_exists = await asyncio.gather(
                    self.vector_db.check_exists(resolved_document_id),
                    self.bm25_store.check_exists(resolved_document_id),
                )
                if dense_exists and bm25_exists:
                    logger.info(
                        "Bỏ qua tài liệu đã được index: %s",
                        resolved_document_id,
                    )
                    return {
                        "status": "skipped",
                        "document_id": resolved_document_id,
                        "chunk_count": 0,
                    }

                chunks = await self.chunker.asplit_file(
                    path,
                    document_id=resolved_document_id,
                    title=title,
                )
                dense_count = await self._index_dense_chunks(chunks)
                await self.bm25_store.upsert(chunks)

                logger.info(
                    "Đã index tài liệu %s với %d chunk",
                    resolved_document_id,
                    len(chunks),
                )
                return {
                    "status": "indexed",
                    "document_id": resolved_document_id,
                    "chunk_count": len(chunks),
                    "dense_count": dense_count,
                    "dense_existed": dense_exists,
                    "bm25_existed": bm25_exists,
                }
            except Exception:
                logger.exception(
                    "Lỗi khi index tài liệu %s",
                    resolved_document_id,
                )
                raise

    async def index_directory(
        self,
        directory: str | Path,
        *,
        recursive: bool = False,
    ) -> list[dict[str, object]]:
        """Index lần lượt tất cả file Markdown trong một thư mục."""
        directory_path = Path(directory)
        if not directory_path.is_dir():
            raise NotADirectoryError(f"Không tìm thấy thư mục: {directory_path}")

        pattern = "**/*.md" if recursive else "*.md"
        file_paths = sorted(directory_path.glob(pattern))
        results: list[dict[str, object]] = []

        logger.info(
            "Bắt đầu index %d file Markdown trong %s",
            len(file_paths),
            directory_path,
        )
        for file_path in file_paths:
            results.append(await self.index_file(file_path))

        logger.info("Đã hoàn thành index %d file Markdown", len(file_paths))
        return results

    async def _index_dense_chunks(self, chunks: list[Chunk]) -> int:
        indexed_count = 0
        batch_size = self.embedder.batch_size

        for start in range(0, len(chunks), batch_size):
            chunk_batch = chunks[start : start + batch_size]
            texts = [self._text_for_embedding(chunk) for chunk in chunk_batch]
            embeddings = await self.embedder.embed_batch(texts)
            points = [
                {
                    "id": chunk.chunk_id,
                    "vector": embedding,
                    "payload": self._chunk_payload(chunk),
                }
                for chunk, embedding in zip(
                    chunk_batch,
                    embeddings,
                    strict=True,
                )
            ]
            await self.vector_db.upsert(points)
            indexed_count += len(points)

        return indexed_count

    @staticmethod
    def _text_for_embedding(chunk: Chunk) -> str:
        metadata = chunk.metadata
        context = filter(
            None,
            [
                metadata.title,
                metadata.section,
                metadata.subsection,
                chunk.content,
            ],
        )
        return "\n".join(context)

    @staticmethod
    def _chunk_payload(chunk: Chunk) -> dict[str, object]:
        return {
            "content": chunk.content,
            "chunk_index": chunk.chunk_index,
            "metadata": chunk.metadata.model_dump(mode="json"),
        }
