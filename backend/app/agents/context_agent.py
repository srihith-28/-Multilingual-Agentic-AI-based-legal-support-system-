"""
Agent Forge - Context Agent

Extracts structured case facts from the user's query and conversation history.
Identifies if critical legal variables are missing and triggers the
Clarification Branch when needed.

Outputs:
    - case_context              : CaseContext Pydantic model with extracted facts
    - needs_clarification       : True if essential facts are missing
    - missing_context_questions : List of targeted clarification questions
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
import google.genai as genai
from google.genai import types

from app.core.config import get_settings
from app.core.state import (
    LegalAgentState,
    CaseContext,
    MarriageAct,
    FamilyLawDomain,
    Language,
)

logger = logging.getLogger("agent_forge.agents.context")
settings = get_settings()


# ------------------------------------------------------------------ #
# Structured Output Schema
# ------------------------------------------------------------------ #

class ExtractedContext(BaseModel):
    religion: Optional[str] = Field(None, description="Religion or community (Hindu, Muslim, Christian, Parsi, or not mentioned)")
    applicable_act: Optional[str] = Field(None, description="Applicable marriage act (HMA, SMA, Muslim, Christian, Parsi, or unknown)")
    marriage_duration_years: Optional[float] = Field(None, description="Duration of marriage in years if mentioned")
    has_minor_children: Optional[bool] = Field(None, description="Whether minor children are involved")
    num_children: Optional[int] = Field(None, description="Number of minor children if mentioned")
    geographic_jurisdiction: Optional[str] = Field(None, description="State or district mentioned")
    prior_proceedings: Optional[str] = Field(None, description="Any existing FIR, complaints, or court orders mentioned")
    income_info: Optional[str] = Field(None, description="Income or financial details relevant to maintenance")
    missing_critical_facts: list[str] = Field(
        default_factory=list,
        description="List of critical facts missing for this specific legal domain"
    )
    clarification_questions: list[str] = Field(
        default_factory=list,
        description="Specific, friendly clarification questions to ask the user if facts are missing"
    )


CONTEXT_SYSTEM_PROMPT = """You are an Indian Family Law case facts extractor.

Your task is to:
1. Extract all relevant legal facts from the user's message and conversation history.
2. Identify which CRITICAL facts are missing based on their legal domain.
3. Generate friendly, specific clarification questions (maximum 2) if critical facts are absent.

Critical facts by domain:
- DIVORCE (any): Religion/applicable act, duration of marriage, mutual or contested grounds
- MAINTENANCE: Income of both parties, separation duration, number of dependents
- DOMESTIC_VIOLENCE: Nature of abuse, whether still living together, any prior complaints/FIR
- CHILD_CUSTODY: Age of children, current living situation, school/education details
- ALL DOMAINS: Geographic state/jurisdiction

Rules:
- If religion/community is not mentioned in a divorce/maintenance query → it's a CRITICAL missing fact
- If marriage duration < 1 year is mentioned → flag the HMA Section 14 one-year bar as relevant
- Generate questions in the SAME language as the user's query (English, Hindi, or Kannada)
- Maximum 2 clarification questions — ask the most critical ones only
- If all critical facts are present, leave missing_critical_facts and clarification_questions EMPTY

Understand English, Hindi, Kannada, Hinglish, and Kanglish queries.
"""


# ------------------------------------------------------------------ #
# Helper: Language-aware clarification preamble
# ------------------------------------------------------------------ #

def _clarification_preamble(lang: str) -> str:
    preambles = {
        "en": "To give you accurate legal information, I need a few more details:",
        "hi": "आपको सटीक कानूनी जानकारी देने के लिए, मुझे कुछ और विवरण चाहिए:",
        "kn": "ನಿಮಗೆ ನಿಖರ ಕಾನೂನು ಮಾಹಿತಿ ನೀಡಲು, ನನಗೆ ಇನ್ನಷ್ಟು ವಿವರಗಳು ಬೇಕು:",
        "te": "మీకు ఖచ్చితమైన చట్టపరమైన సమాచారం అందించడానికి, నాకు మరికొన్ని వివరాలు కావాలి:",
        "ta": "உங்களுக்கு துல்லியமான சட்ட தகவலை வழங்க, எனக்கு மேலும் சில விவரங்கள் தேவை:",
        "bn": "আপনাকে সঠিক আইনি তথ্য দেওয়ার জন্য, আমার আরও কিছু বিবরণ প্রয়োজন:",
        "mr": "तुम्हाला अचूक कायदेशीर माहिती देण्यासाठी, मला आणखी काही तपशील हवे आहेत:",
        "gu": "તમને સચોટ કાનૂની માહિતી આપવા માટે, મને થોડી વધુ વિગતોની જરૂર છે:",
        "ml": "നിങ്ങൾക്ക് കൃത്യമായ നിയമ വിവരങ്ങൾ നൽകാൻ, എനിക്ക് കുറച്ചുകൂടി വിവരങ്ങൾ ആവശ്യമാണ്:",
        "ur": "آپ کو درست قانونی معلومات فراہم کرنے کے لیے، مجھے کچھ مزید تفصیلات درکار ہیں:",
    }
    return preambles.get(lang, preambles["en"])


# ------------------------------------------------------------------ #
# Agent Node
# ------------------------------------------------------------------ #

async def context_node(state: LegalAgentState) -> dict:
    """
    LangGraph node: Extracts case facts and determines if clarification is needed.
    """
    query = state["user_query"]
    domain = state.get("law_domain", FamilyLawDomain.UNKNOWN)
    domain_val = domain.value if hasattr(domain, "value") else str(domain)
    lang_enum = state.get("detected_language", Language.ENGLISH)
    lang = lang_enum.value if hasattr(lang_enum, "value") else str(lang_enum)

    # Include conversation history for multi-turn context
    history_text = ""
    for msg in state.get("conversation_history", [])[-6:]:  # last 3 turns
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_text += f"{role.upper()}: {content}\n"

    logger.info(f"[ContextAgent] Extracting facts for domain: {domain_val}")

    client = genai.Client(api_key=settings.gemini_api_key)

    user_prompt = f"""Legal Domain: {domain_val}
User Language: {lang} (All clarification questions MUST be written in {lang} language and native script!)

Conversation History:
{history_text if history_text else "(No prior conversation)"}

Current Query: "{query}"

Extract all legal case facts and identify any missing critical information."""

    try:
        response = client.models.generate_content(
            model=settings.gemini_llm_model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=CONTEXT_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=ExtractedContext,
                temperature=0.1,
            ),
        )

        extracted: ExtractedContext = response.parsed

        # Build CaseContext object
        act_map = {
            "hma": MarriageAct.HMA,
            "hindu": MarriageAct.HMA,
            "sma": MarriageAct.SMA,
            "special": MarriageAct.SMA,
            "muslim": MarriageAct.MUSLIM,
            "christian": MarriageAct.CHRISTIAN,
            "parsi": MarriageAct.PARSI,
        }
        act_key = (extracted.applicable_act or "").lower()
        applicable_act = next(
            (v for k, v in act_map.items() if k in act_key),
            MarriageAct.UNKNOWN,
        )

        case_context = CaseContext(
            religion=extracted.religion,
            applicable_act=applicable_act,
            marriage_duration_years=extracted.marriage_duration_years,
            has_minor_children=extracted.has_minor_children,
            num_children=extracted.num_children,
            geographic_jurisdiction=extracted.geographic_jurisdiction,
            prior_proceedings=extracted.prior_proceedings,
            income_info=extracted.income_info,
        )

        needs_clarification = len(extracted.missing_critical_facts) > 0

        if needs_clarification:
            logger.info(f"[ContextAgent] Clarification needed: {extracted.missing_critical_facts}")
        else:
            logger.info("[ContextAgent] All critical facts present. Proceeding to Planner.")

        # Clean clarification questions (pure question items without preamble duplication)
        questions = extracted.clarification_questions or []

        return {
            "case_context": case_context,
            "needs_clarification": needs_clarification,
            "missing_context_questions": questions,
        }

    except Exception as e:
        logger.error(f"[ContextAgent] Extraction failed: {e}")
        return {
            "case_context": CaseContext(),
            "needs_clarification": False,
            "missing_context_questions": [],
        }
