"""
Agent Forge - LangGraph State Schema
Defines the complete typed state that flows through all agent nodes.
"""

from typing import Annotated, TypedDict, Optional
from pydantic import BaseModel, Field
from enum import Enum
import operator


# ------------------------------------------------------------------ #
# Enumerations
# ------------------------------------------------------------------ #

class Language(str, Enum):
    """Supported languages for the multilingual system."""
    ENGLISH = "en"
    HINDI = "hi"
    KANNADA = "kn"
    TELUGU = "te"
    TAMIL = "ta"
    BENGALI = "bn"
    MARATHI = "mr"
    GUJARATI = "gu"
    MALAYALAM = "ml"
    URDU = "ur"


class FamilyLawDomain(str, Enum):
    """Family law sub-domains the system can handle."""
    DIVORCE_MUTUAL = "divorce_mutual_consent"
    DIVORCE_CONTESTED = "divorce_contested"
    MAINTENANCE_ALIMONY = "maintenance_alimony"
    DOMESTIC_VIOLENCE = "domestic_violence"
    CHILD_CUSTODY = "child_custody"
    RESTITUTION_CONJUGAL = "restitution_conjugal_rights"
    PROPERTY_SUCCESSION = "property_succession"
    GENERAL_FAMILY_LAW = "general_family_law"
    UNKNOWN = "unknown"


class MarriageAct(str, Enum):
    """Applicable marriage statutes in India."""
    HMA = "Hindu Marriage Act, 1955"
    SMA = "Special Marriage Act, 1954"
    MUSLIM = "Muslim Personal Law (Shariat) Application Act, 1937"
    CHRISTIAN = "Indian Divorce Act, 1869"
    PARSI = "Parsi Marriage and Divorce Act, 1936"
    UNKNOWN = "unknown"


class InputMode(str, Enum):
    """Input modality used by the user."""
    TEXT = "text"
    VOICE = "voice"


class VerificationStatus(str, Enum):
    """Outcome of the Verification Agent check."""
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_CLARIFICATION = "needs_clarification"
    EMERGENCY = "emergency"


# ------------------------------------------------------------------ #
# Sub-models for rich state structure
# ------------------------------------------------------------------ #

class CaseContext(BaseModel):
    """Extracted factual context from the user's conversation."""
    religion: Optional[str] = Field(None, description="User's religion / community")
    applicable_act: MarriageAct = Field(
        default=MarriageAct.UNKNOWN,
        description="Statutory act applicable to the user's marriage",
    )
    marriage_duration_years: Optional[float] = Field(
        None, description="Duration of marriage in years"
    )
    has_minor_children: Optional[bool] = Field(
        None, description="Whether there are minor children involved"
    )
    num_children: Optional[int] = Field(None, description="Number of minor children")
    geographic_jurisdiction: Optional[str] = Field(
        None, description="User's state / district for jurisdictional context"
    )
    prior_proceedings: Optional[str] = Field(
        None, description="Any prior legal proceedings, FIRs, or court orders"
    )
    income_info: Optional[str] = Field(
        None, description="Income information relevant to maintenance claims"
    )


class RetrievedPassage(BaseModel):
    """A single retrieved and reranked legal passage."""
    chunk_id: str
    act_name: str
    section_number: str
    section_title: str
    content: str
    source_url: Optional[str] = None
    relevance_score: float = Field(0.0, description="Cohere reranking score")


class VerificationResult(BaseModel):
    """Structured diagnostic output from the Verification Agent."""
    status: VerificationStatus
    missing_evidence: list[str] = Field(
        default_factory=list,
        description="Specific statutory conditions that are missing from context",
    )
    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="Claims made by the reasoning agent not grounded in retrieved passages",
    )
    revised_search_query: Optional[str] = Field(
        None,
        description="Improved query for the Retrieval Agent on retry",
    )
    retry_count: int = Field(default=0)


class ResponseLayer(BaseModel):
    """The two-layer structured response output."""
    plain_language_summary: str = Field(
        description="Layer 1: Compassionate, jargon-free citizen-readable explanation"
    )
    statutory_citations: list[dict] = Field(
        default_factory=list,
        description="Layer 2: Exact Acts, Section numbers, and official text references",
    )
    disclaimer: str = Field(
        default=(
            "This information is provided for educational and decision-support purposes only. "
            "It does not constitute legal advice. For personalized legal counsel, please consult "
            "a qualified family law advocate or your nearest District Legal Services Authority (DLSA)."
        )
    )
    helplines: Optional[dict] = Field(
        None,
        description="Emergency or legal aid helplines to include in the response",
    )


# ------------------------------------------------------------------ #
# Main LangGraph State TypedDict
# ------------------------------------------------------------------ #

class LegalAgentState(TypedDict):
    """
    The complete state that flows through all LangGraph agent nodes.

    Uses Annotated[list, operator.add] for fields that accumulate across nodes,
    and plain types for fields that get overwritten.
    """

    # --- Input ---
    user_query: str                          # Original user input (text or transcribed voice)
    input_mode: InputMode                    # "text" or "voice"
    audio_file_path: Optional[str]           # Path to uploaded audio file (if voice)

    # --- Language ---
    detected_language: Language              # Detected language of the query
    target_response_language: Language       # Language for the final response

    # --- Safety ---
    is_emergency: bool                       # True if domestic violence / immediate danger detected
    emergency_response: Optional[str]        # Pre-formatted emergency response if is_emergency

    # --- Intent & Domain ---
    law_domain: FamilyLawDomain              # Classified family law sub-domain
    user_intent_summary: str                 # Brief summary of user's legal objective

    # --- Case Context ---
    case_context: Optional[CaseContext]      # Extracted case facts
    missing_context_questions: list[str]     # Clarification questions to ask user if facts missing
    needs_clarification: bool                # Flag: True if agent needs more info from user

    # --- Planning ---
    retrieval_plan: str                      # Planner's search strategy description
    search_query_en: str                     # Normalized English search query for Qdrant
    search_queries_multilingual: list[str]   # Multilingual variations of the search query

    # --- Retrieval ---
    retrieved_passages: Annotated[list[RetrievedPassage], operator.add]  # Accumulates passages
    reranked_passages: list[RetrievedPassage]  # Top-N after Cohere reranking

    # --- Reasoning ---
    reasoning_draft: str                     # Raw reasoning output from Reasoning Agent

    # --- Verification ---
    verification_result: Optional[VerificationResult]  # Diagnostic from Verification Agent
    retry_count: int                         # Current retry loop count

    # --- Response ---
    final_response: Optional[ResponseLayer]  # Structured two-layer response
    audio_output_path: Optional[str]         # Path to TTS-generated audio file

    # --- Conversation Memory (accumulates across turns) ---
    conversation_history: Annotated[list[dict], operator.add]
