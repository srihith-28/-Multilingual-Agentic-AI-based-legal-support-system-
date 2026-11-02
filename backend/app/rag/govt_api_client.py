"""
Agent Forge - Government Legal API Client

Connects to the official India Code API (indiacode.nic.in) to fetch
live statutory text for Indian Family Law Acts.

This client is used in two ways:
1. INGESTION SCRIPT (scripts/ingest_to_qdrant.py):
   Bulk-fetches all family law acts and chunks them for Qdrant indexing.

2. LIVE RETRIEVAL TOOL (Retrieval Agent):
   Fetches specific sections on-demand when the Planner identifies
   that a precise statutory section needs live verification.

Supported via India Code API:
  - Hindu Marriage Act, 1955
  - Special Marriage Act, 1954
  - Protection of Women from Domestic Violence Act, 2005
  - Guardians and Wards Act, 1890
  - Hindu Minority and Guardianship Act, 1956
  - Family Courts Act, 1984
  - Dissolution of Muslim Marriages Act, 1939
  - Indian Divorce Act, 1869
"""

import logging
import asyncio
from typing import Optional

import httpx

from app.core.config import get_settings
from app.core.state import RetrievedPassage

logger = logging.getLogger("agent_forge.rag.govt_api")
settings = get_settings()


# ------------------------------------------------------------------ #
# Act Registry — India Code Act IDs
# ------------------------------------------------------------------ #

FAMILY_LAW_ACTS = {
    "hindu_marriage_act": {
        "name": "Hindu Marriage Act, 1955",
        "act_id": "199503",   # India Code act identifier
        "domain": "divorce_marriage",
    },
    "special_marriage_act": {
        "name": "Special Marriage Act, 1954",
        "act_id": "195402",
        "domain": "divorce_marriage",
    },
    "pwdva": {
        "name": "Protection of Women from Domestic Violence Act, 2005",
        "act_id": "200543",
        "domain": "domestic_violence",
    },
    "guardians_wards_act": {
        "name": "Guardians and Wards Act, 1890",
        "act_id": "189008",
        "domain": "child_custody",
    },
    "hmga": {
        "name": "Hindu Minority and Guardianship Act, 1956",
        "act_id": "195632",
        "domain": "child_custody",
    },
    "family_courts_act": {
        "name": "Family Courts Act, 1984",
        "act_id": "198466",
        "domain": "procedure",
    },
    "dissolution_muslim_marriages": {
        "name": "Dissolution of Muslim Marriages Act, 1939",
        "act_id": "193908",
        "domain": "divorce_marriage",
    },
    "indian_divorce_act": {
        "name": "Indian Divorce Act, 1869",
        "act_id": "186904",
        "domain": "divorce_marriage",
    },
}


# ------------------------------------------------------------------ #
# API Client
# ------------------------------------------------------------------ #

async def fetch_relevant_sections(
    query: str,
    max_results: int = 5,
) -> list[RetrievedPassage]:
    """
    Searches the India Code API for sections relevant to the query.
    Returns a list of RetrievedPassage objects to augment Qdrant results.

    Falls back gracefully if the API key is not configured or the API is unavailable.
    """
    if not settings.govt_legal_api_key:
        logger.debug("[GovtAPI] No API key configured. Skipping live lookup.")
        return []

    try:
        passages = await _search_india_code(query, max_results)
        return passages
    except Exception as e:
        logger.warning(f"[GovtAPI] Live lookup failed (non-critical): {e}")
        return []


async def _search_india_code(query: str, max_results: int) -> list[RetrievedPassage]:
    """Makes an HTTP request to the India Code search API."""
    headers = {
        "Authorization": f"Bearer {settings.govt_legal_api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "query": query,
        "filters": {
            "actType": "CENTRAL_ACT",
            "categories": ["FAMILY", "PERSONAL_LAW", "CRIMINAL"],
        },
        "limit": max_results,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.govt_legal_api_base_url}/search",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    passages = []
    for item in data.get("results", [])[:max_results]:
        passages.append(
            RetrievedPassage(
                chunk_id=f"govt_{item.get('id', 'unknown')}",
                act_name=item.get("actName", "Unknown Act"),
                section_number=item.get("sectionNumber", ""),
                section_title=item.get("sectionTitle", ""),
                content=item.get("sectionText", ""),
                source_url=item.get("url", "https://indiacode.nic.in"),
                relevance_score=item.get("score", 0.5),
            )
        )

    logger.info(f"[GovtAPI] Retrieved {len(passages)} sections from India Code API.")
    return passages


async def fetch_full_act(act_key: str) -> list[dict]:
    """
    Fetches the complete text of a Family Law act by its registry key.
    Used by the ingestion script (scripts/ingest_to_qdrant.py) to bulk-populate Qdrant.

    Args:
        act_key: Key from FAMILY_LAW_ACTS (e.g., 'hindu_marriage_act').

    Returns:
        List of section dicts with act_name, section_number, section_title, content.
    """
    if act_key not in FAMILY_LAW_ACTS:
        raise ValueError(f"Unknown act key: {act_key}. Valid keys: {list(FAMILY_LAW_ACTS.keys())}")

    act_info = FAMILY_LAW_ACTS[act_key]
    act_id = act_info["act_id"]

    headers = {
        "Authorization": f"Bearer {settings.govt_legal_api_key}",
        "Accept": "application/json",
    }

    sections = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{settings.govt_legal_api_base_url}/acts/{act_id}/sections",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    for section in data.get("sections", []):
        sections.append({
            "act_name": act_info["name"],
            "act_key": act_key,
            "domain": act_info["domain"],
            "section_number": section.get("sectionNumber", ""),
            "section_title": section.get("sectionTitle", ""),
            "chapter": section.get("chapter", ""),
            "content": section.get("sectionText", ""),
            "source_url": f"https://indiacode.nic.in/acts/{act_id}/sections/{section.get('id')}",
            "language": "en",
        })

    logger.info(f"[GovtAPI] Fetched {len(sections)} sections from '{act_info['name']}'.")
    return sections
