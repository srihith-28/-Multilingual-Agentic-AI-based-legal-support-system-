"""
Agent Forge - Intent Agent

Classifies the user's legal objective and identifies the specific
Indian Family Law sub-domain applicable to their query.

Outputs:
    - law_domain      : FamilyLawDomain enum value
    - user_intent_summary : Short plain-language description of the intent
"""

import logging
from pydantic import BaseModel, Field
import google.genai as genai
from google.genai import types

from app.core.config import get_settings
from app.core.state import LegalAgentState, FamilyLawDomain

logger = logging.getLogger("agent_forge.agents.intent")
settings = get_settings()


# ------------------------------------------------------------------ #
# Structured Output Schema
# ------------------------------------------------------------------ #

class IntentOutput(BaseModel):
    law_domain: str = Field(
        description=(
            "One of: divorce_mutual_consent, divorce_contested, maintenance_alimony, "
            "domestic_violence, child_custody, restitution_conjugal_rights, "
            "property_succession, general_family_law, unknown"
        )
    )
    user_intent_summary: str = Field(
        description="1-2 sentence plain-language summary of what the user is seeking"
    )
    confidence: float = Field(
        description="Confidence score from 0.0 to 1.0"
    )


INTENT_SYSTEM_PROMPT = """You are a specialized Indian Family Law classifier.
Your job is to analyze user queries and identify their primary legal objective.

Indian Family Law sub-domains you must classify into:
- divorce_mutual_consent    : Divorce with both spouses' agreement (HMA §13B, SMA §28)
- divorce_contested         : Divorce on grounds like cruelty, desertion, adultery (HMA §13)
- maintenance_alimony       : Financial support claims (BNSS §144 / CrPC §125, HMA §24/§25, PWDVA §20)
- domestic_violence         : Physical/emotional/economic abuse, protection orders (PWDVA 2005)
- child_custody             : Guardianship, custody, visitation rights (Guardians & Wards Act 1890, HMGA 1956)
- restitution_conjugal      : Petition to restore marital cohabitation (HMA §9, SMA §22)
- property_succession       : Inheritance, matrimonial property, Stridhan (HSA 1956)
- general_family_law        : General inquiry about family law procedures or rights
- unknown                   : Cannot determine from the query

The user may query in English, Hindi, or Kannada. Understand all three languages.
Identify code-mixed queries (Hinglish, Kanglish) correctly.
"""


# ------------------------------------------------------------------ #
# Agent Node
# ------------------------------------------------------------------ #

async def intent_node(state: LegalAgentState) -> dict:
    """
    LangGraph node: Classifies the user's legal intent and family law domain.
    """
    query = state["user_query"]
    lang = state.get("detected_language", "en")

    logger.info(f"[IntentAgent] Classifying query: '{query[:80]}...' (lang={lang})")

    client = genai.Client(api_key=settings.gemini_api_key)

    user_prompt = f"""User Query (Language: {lang}):
"{query}"

Classify this query into the correct family law domain and summarize the user's intent."""

    try:
        response = client.models.generate_content(
            model=settings.gemini_llm_model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=INTENT_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=IntentOutput,
                temperature=0.1,
            ),
        )

        parsed: IntentOutput = response.parsed

        # Map to enum (default to UNKNOWN if unrecognized)
        try:
            domain = FamilyLawDomain(parsed.law_domain)
        except ValueError:
            domain = FamilyLawDomain.UNKNOWN

        logger.info(f"[IntentAgent] Domain: {domain.value} | Confidence: {parsed.confidence:.2f}")

        return {
            "law_domain": domain,
            "user_intent_summary": parsed.user_intent_summary,
            "conversation_history": [
                {"role": "user", "content": query, "agent": "intent", "domain": domain.value}
            ],
        }

    except Exception as e:
        logger.error(f"[IntentAgent] Classification failed: {e}")
        return {
            "law_domain": FamilyLawDomain.GENERAL_FAMILY_LAW,
            "user_intent_summary": "General family law inquiry.",
        }
