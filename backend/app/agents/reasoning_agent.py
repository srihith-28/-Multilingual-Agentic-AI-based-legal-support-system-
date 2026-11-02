"""
Agent Forge - Reasoning Agent

Synthesizes the reranked legal passages with the user's case context
to produce a grounded, evidence-based legal analysis.

The reasoning agent is explicitly instructed to:
- ONLY use information from the retrieved passages.
- Cite exact Acts and Section numbers.
- Explain both substantive rights AND procedural steps.
- Never fabricate precedents or hallucinate sections.
- Use compassionate, accessible language appropriate for a citizen.

Outputs:
    - reasoning_draft : The raw, evidence-grounded legal analysis
"""

import logging
import google.genai as genai
from google.genai import types

from app.core.config import get_settings
from app.core.state import LegalAgentState, Language

logger = logging.getLogger("agent_forge.agents.reasoning")
settings = get_settings()


# ------------------------------------------------------------------ #
# System Prompt
# ------------------------------------------------------------------ #

REASONING_SYSTEM_PROMPT = """You are a senior Indian Family Law advisor with 20 years of experience.
Your task is to analyze retrieved statutory provisions and apply them to the user's specific situation.

STRICT RULES:
1. ONLY use information from the RETRIEVED LEGAL PASSAGES provided below. Do NOT invent any law.
2. ALWAYS cite the exact Act name and Section number for every legal point you make.
3. If a user mentions details that trigger specific sections (e.g., marriage under 1 year → HMA Section 14),
   explicitly explain the implication.
4. Structure your analysis as:
   a) APPLICABLE LAW: Which Acts and Sections apply and why.
   b) YOUR RIGHTS & REMEDIES: What the law allows the user to seek.
   c) PROCEDURE: Where to file, competent court/authority, approximate timeline, required documents.
   d) IMPORTANT CAVEATS: Waiting periods, conditions, exceptions, or limitations.
5. Write in plain, compassionate language that a non-lawyer can understand.
6. Do NOT give a personal opinion or predict court outcomes.
7. If the retrieved passages are insufficient to answer the question, explicitly state that.
8. Do NOT cite external case citations or ungrounded precedents unless they are explicitly present in the retrieved passages.

You will respond in the user's detected language (English, Hindi, or Kannada).
For Hindi and Kannada responses, use clear, modern language — not archaic legal Sanskrit.
"""


def _format_passages(passages) -> str:
    """Formats reranked passages into a structured context block for the LLM."""
    if not passages:
        return "NO RETRIEVED PASSAGES AVAILABLE."

    formatted = []
    for i, p in enumerate(passages, 1):
        formatted.append(
            f"[PASSAGE {i}] {p.act_name} — {p.section_number}: {p.section_title}\n"
            f"Relevance Score: {p.relevance_score:.4f}\n"
            f"---\n{p.content}\n"
        )
    return "\n\n".join(formatted)


# ------------------------------------------------------------------ #
# Agent Node
# ------------------------------------------------------------------ #

async def reasoning_node(state: LegalAgentState) -> dict:
    """
    LangGraph node: Synthesizes legal reasoning from reranked passages and case context.
    """
    user_query = state["user_query"]
    reranked = state.get("reranked_passages", [])
    case_ctx = state.get("case_context")
    intent = state.get("user_intent_summary", "")
    domain = state.get("law_domain")
    domain_val = domain.value if hasattr(domain, "value") else str(domain) if domain else "family law"
    lang_enum = state.get("detected_language", Language.ENGLISH)
    lang = lang_enum.value if hasattr(lang_enum, "value") else str(lang_enum)

    lang_instruction = {
        "en": "Respond in clear English.",
        "hi": "हिंदी में स्पष्ट और सरल भाषा में उत्तर दें।",
        "kn": "ಸ್ಪಷ್ಟ ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ.",
        "te": "స్పష్టమైన మరియు సులభమైన తెలుగులో సమాధానం ఇవ్వండి.",
        "ta": "தெளிவான மற்றும் எளிய தமிழில் பதிலளிக்கவும்.",
        "bn": "স্পষ্ট এবং সহজ বাংলায় উত্তর দিন।",
        "mr": "स्पष्ट आणि सोप्या मराठीत उत्तर द्या.",
        "gu": "સ્પષ્ટ અને સરળ ગુજરાતીમાં જવાબ આપો.",
        "ml": "വ്യക്തവും ലളിതവുമായ മലയാളത്തിൽ മറുപടി നൽകുക.",
        "ur": "واضح اور آسان اردو میں جواب دیں۔",
    }.get(lang, "Respond in clear English.")

    passages_text = _format_passages(reranked)

    # Build case context summary
    ctx_summary = ""
    if case_ctx:
        ctx_summary = f"""
CASE FACTS:
- Religion/Community: {case_ctx.religion or "Not specified"}
- Applicable Statute: {case_ctx.applicable_act.value if case_ctx.applicable_act else "Unknown"}
- Marriage Duration: {f"{case_ctx.marriage_duration_years} years" if case_ctx.marriage_duration_years else "Not specified"}
- Minor Children: {f"Yes ({case_ctx.num_children})" if case_ctx.has_minor_children else "Not specified"}
- Jurisdiction: {case_ctx.geographic_jurisdiction or "Not specified"}
- Prior Proceedings: {case_ctx.prior_proceedings or "None mentioned"}
- Financial Info: {case_ctx.income_info or "Not mentioned"}
"""

    logger.info(
        f"[ReasoningAgent] Synthesizing from {len(reranked)} passages for domain: "
        f"{domain.value if domain else 'unknown'}"
    )

    client = genai.Client(api_key=settings.gemini_api_key)

    user_prompt = f"""LEGAL DOMAIN: {domain.value if domain else "family law"}
USER INTENT: {intent}
RESPONSE LANGUAGE: {lang} — {lang_instruction}

{ctx_summary}

USER QUERY: "{user_query}"

RETRIEVED LEGAL PASSAGES:
{passages_text}

Based ONLY on the retrieved passages above and the case facts, provide a thorough legal analysis."""

    try:
        response = client.models.generate_content(
            model=settings.gemini_llm_model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=REASONING_SYSTEM_PROMPT,
                temperature=0.3,
                max_output_tokens=2048,
            ),
        )

        reasoning_draft = response.text
        logger.info(f"[ReasoningAgent] Draft generated ({len(reasoning_draft)} chars).")

        return {"reasoning_draft": reasoning_draft}

    except Exception as e:
        logger.error(f"[ReasoningAgent] Reasoning failed: {e}")
        return {
            "reasoning_draft": (
                "I was unable to generate a legal analysis at this time due to a technical error. "
                "Please consult your nearest District Legal Services Authority (DLSA) for free legal aid."
            )
        }
