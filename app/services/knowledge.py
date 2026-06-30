"""Persistent local vector memory and semantic retrieval.

The local backend uses a sparse hashing embedding, cosine similarity, and a
lexical reranker. It has no model download and is suitable for tests and local
development. The storage contract is deliberately backend-neutral so Chroma,
FAISS, Qdrant, or Pinecone adapters can be selected behind the same service.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Iterable

from app.database.repository import Repository


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{1,}")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def embed(text: str, dimensions: int = 384) -> dict[str, float]:
    counts: Counter[int] = Counter()
    for token in tokenize(text):
        index = int(hashlib.sha256(token.encode()).hexdigest()[:8], 16) % dimensions
        counts[index] += 1
    norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {str(index): value / norm for index, value in counts.items()}


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > size:
            chunks.append(current)
            current = current[-overlap:] + "\n\n" + paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks or ([text] if text else [])


class KnowledgeBase:
    def __init__(self, repository: Repository, chunk_size: int = 900):
        self.repository = repository
        self.chunk_size = chunk_size

    async def add_report(self, report_id: str, topic: str, content: str) -> int:
        chunks = [
            {"content": item, "embedding": embed(item)}
            for item in chunk_text(content, self.chunk_size)
        ]
        import asyncio

        await asyncio.to_thread(
            self.repository.replace_chunks, report_id, topic, chunks
        )
        return len(chunks)

    async def search(self, query: str, limit: int = 5) -> list[dict]:
        import asyncio

        rows = await asyncio.to_thread(self.repository.all_chunks)
        query_embedding = embed(query)
        query_terms = set(tokenize(query))
        ranked = []
        for row in rows:
            semantic = cosine(query_embedding, row["embedding"])
            terms = set(tokenize(row["content"]))
            lexical = len(query_terms & terms) / max(len(query_terms), 1)
            score = semantic * 0.75 + lexical * 0.25
            ranked.append(
                {
                    "report_id": row["report_id"],
                    "topic": row["topic"],
                    "content": row["content"],
                    "score": round(score, 4),
                    "position": row["position"],
                }
            )
        return sorted(ranked, key=lambda item: item["score"], reverse=True)[:limit]
