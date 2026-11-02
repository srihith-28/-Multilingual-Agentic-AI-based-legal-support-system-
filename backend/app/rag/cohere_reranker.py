"""
Agent Forge - Cohere Multilingual Reranker

Uses Cohere's rerank-multilingual-v3.0 to reorder Qdrant candidate passages
by their relevance to the user's actual query, dramatically improving precision.
"""

import logging
import asyncio
from typing import Optional

import cohere

from app.core.config import get_settings
from app.core.state import RetrievedPassage

logger = logging.getLogger("agent_forge.rag.reranker")
settings = get_settings()


# ------------------------------------------------------------------ #
# Client Singleton  (sync Client — run via asyncio.to_thread)
# ------------------------------------------------------------------ #

_cohere_client: Optional[cohere.Client] = None


def get_cohere_client() -> cohere.Client:
    """Returns the singleton Cohere Client."""
    global _cohere_client
    if _cohere_client is None:
        _cohere_client = cohere.Client(api_key=settings.cohere_api_key)
        logger.info("✅ Cohere Client initialized.")
    return _cohere_client


# ------------------------------------------------------------------ #
# Reranking Function
# ------------------------------------------------------------------ #

async def rerank_passages(
    query: str,
    passages: list[RetrievedPassage],
    top_n: int = None,
) -> list[RetrievedPassage]:
    """
    Reranks a list of retrieved passages using Cohere's multilingual reranker.

    Args:
        query    : The user's search query (can be in English, Hindi, or Kannada).
        passages : List of candidate passages from Qdrant hybrid search.
        top_n    : Number of top passages to return (defaults to settings.cohere_rerank_top_n).

    Returns:
        Reranked list of RetrievedPassage objects (top_n results, sorted by relevance).
    """
    top_n = top_n or settings.cohere_rerank_top_n

    if not passages:
        logger.warning("[Cohere] No passages to rerank. Returning empty list.")
        return []

    if len(passages) <= top_n:
        logger.info(f"[Cohere] Only {len(passages)} passages available. Skipping reranking.")
        return passages

    logger.info(
        f"[Cohere] Reranking {len(passages)} passages → top {top_n} "
        f"using {settings.cohere_rerank_model}"
    )

    # Build document texts: act name + section + content
    documents = [
        f"{p.act_name} — Section {p.section_number}: {p.section_title}\n\n{p.content}"
        for p in passages
    ]

    def _do_rerank():
        client = get_cohere_client()
        return client.rerank(
            model=settings.cohere_rerank_model,
            query=query,
            documents=documents,
            top_n=top_n,
        )

    try:
        result = await asyncio.to_thread(_do_rerank)

        reranked: list[RetrievedPassage] = []
        for item in result.results:
            passage = passages[item.index]
            reranked_passage = passage.model_copy(
                update={"relevance_score": item.relevance_score}
            )
            reranked.append(reranked_passage)

        if reranked:
            logger.info(
                f"[Cohere] Reranking complete. Top score: {reranked[0].relevance_score:.4f} "
                f"({reranked[0].act_name} — {reranked[0].section_number})"
            )
        return reranked

    except Exception as e:
        logger.error(f"[Cohere] Reranking failed: {e}. Falling back to Qdrant scores.")
        return sorted(passages, key=lambda p: p.relevance_score, reverse=True)[:top_n]
