"""
Agent Forge - Retrieval Agent

Executes the hybrid RAG pipeline using the search plan from the Planner Agent:
1. Runs Hybrid Qdrant Search (Dense + BM25) with the normalized English query.
2. Optionally calls the Government Legal API for live statutory lookups.
3. Passes all candidates through the Cohere Multilingual Reranker.
4. Stores the reranked top-N passages in state for the Reasoning Agent.

Outputs:
    - retrieved_passages : Raw Qdrant passages (accumulated in state)
    - reranked_passages  : Top-N after Cohere reranking
    - retry_count        : Incremented on each retry loop
"""

import logging

from app.core.config import get_settings
from app.core.state import LegalAgentState
from app.rag.qdrant_client import hybrid_search
from app.rag.cohere_reranker import rerank_passages

logger = logging.getLogger("agent_forge.agents.retrieval")
settings = get_settings()


async def retrieval_node(state: LegalAgentState) -> dict:
    """
    LangGraph node: Hybrid RAG retrieval + Cohere reranking.
    Uses structured diagnostic feedback from VerificationResult on retry.
    """
    search_query = state.get("search_query_en", "")
    user_query = state["user_query"]
    retry_count = state.get("retry_count", 0)
    verification_result = state.get("verification_result")

    # On retry: use the revised search query from VerificationAgent diagnostic
    if retry_count > 0 and verification_result and verification_result.revised_search_query:
        search_query = verification_result.revised_search_query
        logger.info(
            f"[RetrievalAgent] Retry #{retry_count} — using revised query: '{search_query[:80]}...'"
        )
    else:
        logger.info(f"[RetrievalAgent] Primary search: '{search_query[:80]}...'")

    # ── Step 1: Hybrid Qdrant Search ──────────────────────────────────
    raw_passages = await hybrid_search(
        query_en=search_query,
        top_k=settings.qdrant_top_k,
    )

    # ── Step 2: Government API Live Lookup (if enabled) ───────────────
    if settings.govt_legal_api_key:
        try:
            from app.rag.govt_api_client import fetch_relevant_sections
            govt_passages = await fetch_relevant_sections(search_query)
            if govt_passages:
                logger.info(f"[RetrievalAgent] Gov API returned {len(govt_passages)} additional passages.")
                raw_passages = raw_passages + govt_passages
        except Exception as e:
            logger.warning(f"[RetrievalAgent] Government API lookup failed (non-critical): {e}")

    if not raw_passages:
        logger.warning("[RetrievalAgent] No passages retrieved. Returning empty.")
        return {
            "retrieved_passages": [],
            "reranked_passages": [],
            "retry_count": retry_count + 1,
        }

    # ── Step 3: Cohere Multilingual Reranking ─────────────────────────
    # Use the original user query for reranking (captures true intent better
    # than the normalized English query alone)
    reranked = await rerank_passages(
        query=user_query,
        passages=raw_passages,
        top_n=settings.cohere_rerank_top_n,
    )

    logger.info(
        f"[RetrievalAgent] Retrieved: {len(raw_passages)} | "
        f"Reranked to top-{len(reranked)}: "
        + ", ".join([f"{p.act_name} §{p.section_number}" for p in reranked[:3]])
    )

    return {
        "retrieved_passages": raw_passages,   # Accumulated in state via operator.add
        "reranked_passages": reranked,
        "retry_count": retry_count + 1,
    }
