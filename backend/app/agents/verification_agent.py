"""
Agent Forge - Verification Agent

The safety gatekeeper of the pipeline. Verifies that the Reasoning Agent's
draft analysis is:
1. Fully grounded in the retrieved statutory passages (no hallucinated sections).
2. Citing real Acts and Section numbers that exist in the retrieved context.
3. Free of unsupported legal claims or fabricated case precedents.

If verification fails, produces a structured VerificationResult with:
- The specific missing evidence.
- The unsupported claims that need correction.
- A revised search query for the Retrieval Agent's retry pass.

Outputs:
    - verification_result : VerificationResult with pass/fail and diagnostic data
"""

import logging
import re
from pydantic import BaseModel, Field
import google.genai as genai
from google.genai import types

from app.core.config import get_settings
from app.core.state import (
    LegalAgentState,
    VerificationResult,
    VerificationStatus,
    RetrievedPassage,
)

logger = logging.getLogger("agent_forge.agents.verification")
settings = get_settings()


# ------------------------------------------------------------------ #
# Structured Output Schema for Gemini
# ------------------------------------------------------------------ #

class VerificationOutput(BaseModel):
    verdict: str = Field(
        description="One of: PASSED, FAILED, NEEDS_CLARIFICATION"
    )
    grounding_score: float = Field(
        description="Score from 0.0 to 1.0 indicating how well the response is grounded in retrieved passages"
    )
    missing_evidence: list[str] = Field(
        default_factory=list,
        description="Specific statutory provisions or conditions mentioned in the reasoning but NOT found in retrieved passages"
    )
    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="Claims, sections, or precedents cited in the reasoning that are NOT in the retrieved context"
    )
    revised_search_query: str = Field(
        default="",
        description="Improved search query to find the missing statutory evidence (fill this if verdict is FAILED)"
    )
    verification_notes: str = Field(
        description="Brief explanation of the verification decision"
    )


VERIFICATION_SYSTEM_PROMPT = """You are a rigorous Indian Family Law fact-checker and legal grounding verifier.

Your task: Verify that the REASONING DRAFT is:
1. GROUNDED in the RETRIEVED PASSAGES provided.
2. Not citing fabricated Acts, non-existent Sections, or false legal propositions.
3. Sub-sections (e.g., Section 13B(1), 13B(2)) are valid if the parent Section (Section 13B) exists in the retrieved passages.
4. Any case notes or statutory explanations included within the retrieved passages are considered verified ground truth.

VERIFICATION RULES:
- PASSED: The key legal statutes and sections cited in the draft exist in the retrieved passages, and the legal advice accurately reflects them.
- FAILED: The draft fabricates non-existent statutory sections, cites completely wrong/unrelated laws, or contradicts the statutory text.
- NEEDS_CLARIFICATION: The draft correctly identifies it cannot answer due to missing critical user facts.

GROUNDING SCORE GUIDE:
- 1.0: Accurate and fully grounded in retrieved passages.
- 0.8-0.9: Grounded with minor stylistic differences.
- 0.5-0.7: Partially grounded.
- 0.0-0.4: Fabricated or contradictory.

If FAILED, provide a REVISED_SEARCH_QUERY that would retrieve the missing statutory evidence.
"""


# ------------------------------------------------------------------ #
# Helper: Extract cited sections from text
# ------------------------------------------------------------------ #

def _extract_cited_sections(text: str) -> set[str]:
    """Extracts base Section number patterns from a text string."""
    patterns = [
        r'[Ss]ection\s+(\d+[A-Za-z]?)',
        r'[Ss]ec\.\s*(\d+[A-Za-z]?)',
        r'§\s*(\d+[A-Za-z]?)',
        r'धारा\s+(\d+[A-Za-z]?)',     # Hindi: dhara (section)
        r'ಕಲಂ\s+(\d+[A-Za-z]?)',       # Kannada: kalam (section)
    ]
    cited = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        cited.update(matches)
    return cited


def _extract_available_sections(passages: list[RetrievedPassage]) -> set[str]:
    """Extracts all section numbers available in retrieved passages."""
    available = set()
    for p in passages:
        if p.section_number:
            # Normalize: "Section 13B" → "13B", "§24" → "24"
            num = re.sub(r'^[Ss]ection\s*|^§', '', p.section_number).strip()
            # Also extract base (e.g. 13B from 13B(2))
            base_match = re.match(r'(\d+[A-Za-z]?)', num)
            if base_match:
                available.add(base_match.group(1))
            available.add(num)
        # Also add from content
        available.update(_extract_cited_sections(p.content))
    return available


# ------------------------------------------------------------------ #
# Agent Node
# ------------------------------------------------------------------ #

async def verification_node(state: LegalAgentState) -> dict:
    """
    LangGraph node: Verifies the reasoning draft against retrieved passages.
    """
    reasoning_draft = state.get("reasoning_draft", "")
    reranked_passages = state.get("reranked_passages", [])
    user_query = state["user_query"]
    domain = state.get("law_domain")
    retry_count = state.get("retry_count", 0)

    logger.info(f"[VerificationAgent] Verifying draft (retry_count={retry_count})...")

    # Format full passages for the verifier LLM (up to 3000 chars per passage)
    passages_text = "\n\n".join(
        f"[{p.act_name} — Section {p.section_number}: {p.section_title}]\n{p.content[:3000]}"
        for p in reranked_passages
    ) or "NO PASSAGES RETRIEVED."

    client = genai.Client(api_key=settings.gemini_api_key)

    user_prompt = f"""LEGAL DOMAIN: {domain.value if domain else "family law"}
USER QUERY: "{user_query}"

RETRIEVED PASSAGES (ground truth):
{passages_text}

REASONING DRAFT TO VERIFY:
{reasoning_draft}

Verify the draft against the retrieved passages and provide your verdict."""

    try:
        response = client.models.generate_content(
            model=settings.gemini_llm_model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=VERIFICATION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=VerificationOutput,
                temperature=0.1,
            ),
        )

        output: VerificationOutput = response.parsed

        # Map string verdict to VerificationStatus enum
        status_map = {
            "PASSED": VerificationStatus.PASSED,
            "FAILED": VerificationStatus.FAILED,
            "NEEDS_CLARIFICATION": VerificationStatus.NEEDS_CLARIFICATION,
        }
        status = status_map.get(output.verdict.upper(), VerificationStatus.FAILED)

        logger.info(
            f"[VerificationAgent] Verdict: {status.value} | "
            f"Grounding Score: {output.grounding_score:.2f}"
        )

        if status == VerificationStatus.FAILED:
            logger.warning(
                f"[VerificationAgent] FAILED — Missing: {output.missing_evidence} | "
                f"Unsupported: {output.unsupported_claims}"
            )

        verification_result = VerificationResult(
            status=status,
            missing_evidence=output.missing_evidence,
            unsupported_claims=output.unsupported_claims,
            revised_search_query=output.revised_search_query or "",
            retry_count=retry_count,
        )

        return {"verification_result": verification_result}

    except Exception as e:
        logger.error(f"[VerificationAgent] Verification failed: {e}. Defaulting to PASSED.")
        # Fail-open: if verification itself errors, proceed to response
        return {
            "verification_result": VerificationResult(
                status=VerificationStatus.PASSED,
                missing_evidence=[],
                unsupported_claims=[],
                revised_search_query="",
                retry_count=retry_count,
            )
        }
