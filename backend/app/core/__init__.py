"""
Agent Forge - Core Package Init
"""
from .config import get_settings, Settings
from .state import (
    LegalAgentState,
    Language,
    FamilyLawDomain,
    MarriageAct,
    InputMode,
    VerificationStatus,
    CaseContext,
    RetrievedPassage,
    VerificationResult,
    ResponseLayer,
)

__all__ = [
    "get_settings",
    "Settings",
    "LegalAgentState",
    "Language",
    "FamilyLawDomain",
    "MarriageAct",
    "InputMode",
    "VerificationStatus",
    "CaseContext",
    "RetrievedPassage",
    "VerificationResult",
    "ResponseLayer",
]
