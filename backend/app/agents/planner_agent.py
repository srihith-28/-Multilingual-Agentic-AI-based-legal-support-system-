"""
Agent Forge - Planner Agent

Formulates a precise retrieval strategy based on the user's intent and
extracted case context. Decides which statutory acts to search, which
sections are most likely relevant, and generates normalized English
search queries for the Hybrid RAG pipeline.

Outputs:
    - retrieval_plan             : Detailed search strategy description
    - search_query_en            : Primary normalized English query for Qdrant
    - search_queries_multilingual: Multilingual query variants
"""

import logging
from pydantic import BaseModel, Field
import google.genai as genai
from google.genai import types

from app.core.config import get_settings
from app.core.state import LegalAgentState, FamilyLawDomain, MarriageAct, Language

logger = logging.getLogger("agent_forge.agents.planner")
settings = get_settings()


# ------------------------------------------------------------------ #
# Structured Output Schema
# ------------------------------------------------------------------ #

class PlannerOutput(BaseModel):
    retrieval_plan: str = Field(
        description="Step-by-step description of the retrieval strategy"
    )
    primary_search_query_en: str = Field(
        description="Primary search query in English optimized for vector + BM25 hybrid search"
    )
    search_query_hi: str = Field(
        description="Hindi translation of the primary search query"
    )
    search_query_kn: str = Field(
        description="Kannada translation of the primary search query"
    )
    target_acts: list[str] = Field(
        description="List of statutory acts to prioritize (e.g., ['Hindu Marriage Act 1955', 'PWDVA 2005'])"
    )
    target_sections: list[str] = Field(
        description="Specific section numbers likely relevant (e.g., ['Section 13B', 'Section 24', 'Section 125'])"
    )


# ------------------------------------------------------------------ #
# Domain → Default Acts & Key Sections Mapping
# ------------------------------------------------------------------ #

DOMAIN_ACT_MAP = {
    FamilyLawDomain.DIVORCE_MUTUAL: {
        MarriageAct.HMA: ["Section 13B", "Section 14"],
        MarriageAct.SMA: ["Section 28"],
        MarriageAct.UNKNOWN: ["Section 13B HMA", "Section 28 SMA", "mutual consent divorce"],
    },
    FamilyLawDomain.DIVORCE_CONTESTED: {
        MarriageAct.HMA: ["Section 13", "Section 9", "Section 14"],
        MarriageAct.SMA: ["Section 27"],
        MarriageAct.UNKNOWN: ["Section 13 HMA grounds divorce cruelty desertion adultery"],
    },
    FamilyLawDomain.MAINTENANCE_ALIMONY: {
        MarriageAct.HMA: ["Section 24", "Section 25"],
        MarriageAct.UNKNOWN: ["Section 144 BNSS", "Section 125 CrPC", "maintenance alimony spouse children"],
    },
    FamilyLawDomain.DOMESTIC_VIOLENCE: {
        MarriageAct.UNKNOWN: [
            "Section 12 PWDVA protection order",
            "Section 17 right to reside shared household",
            "Section 18 protection order",
            "Section 19 residence order",
            "Section 20 monetary relief",
            "Section 21 custody order",
            "Section 22 compensation order",
            "Section 23 interim ex-parte relief",
        ],
    },
    FamilyLawDomain.CHILD_CUSTODY: {
        MarriageAct.UNKNOWN: [
            "Section 26 HMA custody",
            "Guardians and Wards Act 1890 Section 7 Section 17",
            "Hindu Minority Guardianship Act 1956 Section 6 Section 13",
            "welfare of child best interest custody",
        ],
    },
    FamilyLawDomain.RESTITUTION_CONJUGAL: {
        MarriageAct.HMA: ["Section 9"],
        MarriageAct.SMA: ["Section 22"],
        MarriageAct.UNKNOWN: ["restitution conjugal rights Section 9 HMA Section 22 SMA"],
    },
}

PLANNER_SYSTEM_PROMPT = """You are an Indian Family Law retrieval strategist.

Your task is to analyze the user's legal domain, case context, and intent, then formulate
an optimal search strategy to retrieve the most relevant statutory provisions from a
multilingual vector database (Qdrant with BM25 + dense search).

Rules:
1. The primary_search_query_en must be in English and optimized for both semantic meaning
   AND exact section number keyword matching (e.g., "Section 13B mutual consent divorce
   one year separation cooling off period Hindu Marriage Act 1955").
2. Include both plain-language concepts AND exact statutory terminology.
3. The Hindi and Kannada queries should be faithful translations.
4. Target acts and sections must be specific and correct under Indian law.
5. If the applicable act is unknown, include queries for all possible applicable acts.
"""


# ------------------------------------------------------------------ #
# Agent Node
# ------------------------------------------------------------------ #

async def planner_node(state: LegalAgentState) -> dict:
    """
    LangGraph node: Formulates the retrieval strategy and search queries.
    """
    domain = state.get("law_domain", FamilyLawDomain.UNKNOWN)
    domain_val = domain.value if hasattr(domain, "value") else str(domain)
    intent_summary = state.get("user_intent_summary", "")
    case_ctx = state.get("case_context")
    query = state["user_query"]
    lang_enum = state.get("detected_language", Language.ENGLISH)
    lang = lang_enum.value if hasattr(lang_enum, "value") else "en"

    # Get domain-specific hints
    applicable_act = case_ctx.applicable_act if case_ctx else MarriageAct.UNKNOWN
    act_val = applicable_act.value if hasattr(applicable_act, "value") else str(applicable_act)
    domain_hints = DOMAIN_ACT_MAP.get(domain, {})
    act_hints = domain_hints.get(applicable_act, domain_hints.get(MarriageAct.UNKNOWN, []))

    # Verification retry: incorporate diagnostic feedback if this is a retry
    verification_result = state.get("verification_result")
    retry_context = ""
    if verification_result and verification_result.revised_search_query:
        retry_context = f"\n\nPREVIOUS SEARCH FAILED. Revised focus: {verification_result.revised_search_query}"
        retry_context += f"\nMissing evidence: {', '.join(verification_result.missing_evidence)}"

    logger.info(f"[PlannerAgent] Domain: {domain_val} | Act: {act_val} | Retry: {state.get('retry_count', 0)}")

    client = genai.Client(api_key=settings.gemini_api_key)

    user_prompt = f"""Legal Domain: {domain_val}
Applicable Act: {act_val}
User Language: {lang}
User Intent: {intent_summary}
Original Query: "{query}"

Case Context:
- Religion/Community: {case_ctx.religion if case_ctx else "Unknown"}
- Marriage Duration: {case_ctx.marriage_duration_years if case_ctx else "Unknown"} years
- Minor Children: {case_ctx.has_minor_children if case_ctx else "Unknown"}
- Jurisdiction: {case_ctx.geographic_jurisdiction if case_ctx else "Unknown"}

Known Relevant Sections for this domain: {act_hints}
{retry_context}

Formulate an optimal retrieval plan and search queries."""

    try:
        response = client.models.generate_content(
            model=settings.gemini_llm_model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=PLANNER_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=PlannerOutput,
                temperature=0.2,
            ),
        )

        plan: PlannerOutput = response.parsed

        logger.info(f"[PlannerAgent] Primary query: '{plan.primary_search_query_en[:80]}...'")
        logger.info(f"[PlannerAgent] Target acts: {plan.target_acts}")
        logger.info(f"[PlannerAgent] Target sections: {plan.target_sections}")

        return {
            "retrieval_plan": plan.retrieval_plan,
            "search_query_en": plan.primary_search_query_en,
            "search_queries_multilingual": [
                plan.primary_search_query_en,
                plan.search_query_hi,
                plan.search_query_kn,
            ],
        }

    except Exception as e:
        logger.error(f"[PlannerAgent] Planning failed: {e}")
        # Fallback: use the original query + domain hints
        fallback_query = f"{intent_summary} {' '.join(act_hints[:3])} {query}"
        return {
            "retrieval_plan": f"Fallback search for {domain_val}",
            "search_query_en": fallback_query[:500],
            "search_queries_multilingual": [fallback_query[:500]],
        }
