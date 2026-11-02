"""
Agent Forge - Qdrant Hybrid Search Client

Provides hybrid search (Dense multilingual vectors + BM25 sparse keyword)
on the Qdrant Cloud vector database containing Indian Family Law statutory chunks.

Key Features:
- Dense vector search: Captures semantic/conceptual meaning of queries.
- BM25 sparse search: Guarantees retrieval accuracy for exact section numbers
  (e.g., "Section 13B", "Section 125", "Section 498A").
- Payload filtering: Filter by act_name, section_number, language, etc.
- Async-compatible using asyncio.to_thread for blocking Qdrant calls.
"""

import logging
import asyncio
from typing import Optional

from qdrant_client import QdrantClient, models as qdrant_models
from qdrant_client.http.models import (
    Filter,
    FieldCondition,
    MatchValue,
)

from app.core.config import get_settings
from app.core.state import RetrievedPassage

logger = logging.getLogger("agent_forge.rag.qdrant")
settings = get_settings()

# Vector names in the Qdrant collection
DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"


# ------------------------------------------------------------------ #
# Client Singleton
# ------------------------------------------------------------------ #

_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """Returns the singleton Qdrant Cloud client."""
    global _client
    if _client is None:
        _client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=30,
            check_compatibility=False,
        )
        logger.info(f"✅ Qdrant client initialized: {settings.qdrant_url}")
    return _client


# ------------------------------------------------------------------ #
# Embedding Function (Gemini text-embedding-004)
# ------------------------------------------------------------------ #

async def embed_query(text: str) -> list[float]:
    """
    Generates a dense multilingual embedding for the query using Gemini.
    text-embedding-004 supports 100+ languages including Hindi and Kannada.
    """
    import google.genai as genai
    from google.genai import types as genai_types

    client = genai.Client(api_key=settings.gemini_api_key)

    def _embed():
        try:
            result = client.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=text,
                config=genai_types.EmbedContentConfig(output_dimensionality=768),
            )
            return result.embeddings[0].values
        except Exception:
            # Fallback: call without dimensionality config
            result = client.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=text,
            )
            return result.embeddings[0].values

    return await asyncio.to_thread(_embed)


# ------------------------------------------------------------------ #
# BM25 Tokenizer (for sparse vector)
# ------------------------------------------------------------------ #

def _bm25_tokenize(text: str) -> dict[int, float]:
    """
    Simple BM25-style sparse tokenizer.
    Maps token hashes to TF-IDF-like weights.
    In production, use fastembed's BM25 encoder for accuracy.
    """
    import re
    from collections import Counter

    # Normalize and tokenize
    text = text.lower()
    # Keep alphanumeric, section numbers (e.g., 13b, 125)
    tokens = re.findall(r'\b[a-z0-9]+\b', text)

    if not tokens:
        return {}

    counts = Counter(tokens)
    total = sum(counts.values())

    # Term frequency weights (simple TF)
    sparse = {}
    for token, count in counts.items():
        token_hash = abs(hash(token)) % 100_000  # Map to sparse dimension space
        sparse[token_hash] = count / total

    return sparse


# ------------------------------------------------------------------ #
# Hybrid Search
# ------------------------------------------------------------------ #

async def hybrid_search(
    query_en: str,
    top_k: int = None,
    act_name_filter: Optional[str] = None,
) -> list[RetrievedPassage]:
    """
    Performs hybrid dense + sparse (BM25) search on the Qdrant collection.

    Args:
        query_en       : English search query (normalized by Planner/Retrieval Agent)
        top_k          : Number of results to retrieve (defaults to settings.qdrant_top_k)
        act_name_filter: Optional act name to filter results (e.g., "Hindu Marriage Act")

    Returns:
        List of RetrievedPassage objects with metadata and relevance scores.
    """
    top_k = top_k or settings.qdrant_top_k
    client = get_qdrant_client()

    logger.info(f"[Qdrant] Hybrid search: '{query_en[:60]}...' | Top-K: {top_k}")

    # 1. Generate dense embedding
    dense_vector = await embed_query(query_en)

    # 2. Build sparse vector (BM25 tokens)
    sparse_tokens = _bm25_tokenize(query_en)
    if sparse_tokens:
        sparse_indices = sorted(sparse_tokens.keys())
        sparse_values = [sparse_tokens[k] for k in sparse_indices]
    else:
        sparse_indices = [0]
        sparse_values = [1.0]

    # 3. Build optional metadata filter
    query_filter = None
    if act_name_filter:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="act_name",
                    match=MatchValue(value=act_name_filter),
                )
            ]
        )

    def _run_hybrid_search():
        """Execute hybrid search (blocking, run in thread)."""
        try:
            # Try hybrid search with prefetch (Qdrant v1.7+)
            results = client.query_points(
                collection_name=settings.qdrant_collection,
                prefetch=[
                    # Dense semantic search
                    qdrant_models.Prefetch(
                        query=dense_vector,
                        using=DENSE_VECTOR_NAME,
                        limit=top_k * 2,
                    ),
                    # Sparse BM25 keyword search
                    qdrant_models.Prefetch(
                        query=qdrant_models.SparseVector(
                            indices=sparse_indices,
                            values=sparse_values,
                        ),
                        using=SPARSE_VECTOR_NAME,
                        limit=top_k * 2,
                    ),
                ],
                # Reciprocal Rank Fusion to merge results
                query=qdrant_models.FusionQuery(fusion=qdrant_models.Fusion.RRF),
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
            )
            return results.points
        except Exception:
            # Fallback: pure dense search (if collection doesn't have sparse vectors yet)
            logger.warning("[Qdrant] Hybrid search failed, falling back to dense-only search.")
            results = client.search(
                collection_name=settings.qdrant_collection,
                query_vector=(DENSE_VECTOR_NAME, dense_vector),
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
            )
            return results

    raw_results = await asyncio.to_thread(_run_hybrid_search)

    # 4. Parse results into RetrievedPassage objects
    passages: list[RetrievedPassage] = []
    for hit in raw_results:
        payload = hit.payload or {}
        passages.append(
            RetrievedPassage(
                chunk_id=str(hit.id),
                act_name=payload.get("act_name", "Unknown Act"),
                section_number=payload.get("section_number", ""),
                section_title=payload.get("section_title", ""),
                content=payload.get("content", ""),
                source_url=payload.get("source_url"),
                relevance_score=getattr(hit, "score", 0.0) or 0.0,
            )
        )

    logger.info(f"[Qdrant] Retrieved {len(passages)} passages.")
    return passages


# ------------------------------------------------------------------ #
# Collection Setup Helper (for ingestion script)
# ------------------------------------------------------------------ #

def setup_collection(embedding_dim: int = 768) -> None:
    """
    Creates the Qdrant collection with hybrid (dense + sparse) vector config.
    Call this once during initial setup / ingestion.

    Args:
        embedding_dim: Dimension of the dense embedding model.
                       text-embedding-004 = 768 dims.
    """
    client = get_qdrant_client()
    collection_name = settings.qdrant_collection

    existing = [c.name for c in client.get_collections().collections]
    if collection_name in existing:
        logger.info(f"[Qdrant] Collection '{collection_name}' already exists. Skipping creation.")
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            DENSE_VECTOR_NAME: qdrant_models.VectorParams(
                size=embedding_dim,
                distance=qdrant_models.Distance.COSINE,
                on_disk=True,
            ),
        },
        sparse_vectors_config={
            SPARSE_VECTOR_NAME: qdrant_models.SparseVectorParams(
                index=qdrant_models.SparseIndexParams(on_disk=True),
            ),
        },
        optimizers_config=qdrant_models.OptimizersConfigDiff(
            indexing_threshold=10_000,
        ),
    )

    # Create payload indexes for fast metadata filtering
    for field in ["act_name", "section_number", "language", "domain"]:
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
        )

    logger.info(f"✅ Qdrant collection '{collection_name}' created with hybrid vector config.")
