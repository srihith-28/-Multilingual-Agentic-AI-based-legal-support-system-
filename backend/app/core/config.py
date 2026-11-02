"""
Agent Forge - Core Configuration
Loads and validates all environment variables using Pydantic Settings.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
from typing import Literal

# Resolve .env path relative to the backend/ directory (two levels up from this file)
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """
    Centralized configuration object for Agent Forge.
    All settings are loaded from the .env file and environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Google Gemini
    # ------------------------------------------------------------------ #
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_llm_model: str = Field(
        default="gemini-3.5-flash-lite",
        description="Gemini model for reasoning agents",
    )
    gemini_embedding_model: str = Field(
        default="gemini-embedding-001",
        description="Gemini multilingual embedding model",
    )

    # ------------------------------------------------------------------ #
    # Cohere
    # ------------------------------------------------------------------ #
    cohere_api_key: str = Field(..., description="Cohere API key for reranking")
    cohere_rerank_model: str = Field(
        default="rerank-multilingual-v3.0",
        description="Cohere multilingual reranker model",
    )

    # ------------------------------------------------------------------ #
    # Qdrant
    # ------------------------------------------------------------------ #
    qdrant_url: str = Field(..., description="Qdrant Cloud cluster URL")
    qdrant_api_key: str = Field(..., description="Qdrant Cloud API key")
    qdrant_collection: str = Field(
        default="indian_family_law",
        description="Qdrant vector collection name",
    )

    # ------------------------------------------------------------------ #
    # Government Legal API
    # ------------------------------------------------------------------ #
    govt_legal_api_key: str = Field(
        default="",
        description="Official Government Legal Knowledge Base API key",
    )
    govt_legal_api_base_url: str = Field(
        default="https://api.indiacode.nic.in/api",
        description="Base URL for India Code / Government Legal API",
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    app_env: Literal["development", "production"] = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")

    # ------------------------------------------------------------------ #
    # LangGraph Checkpointing
    # ------------------------------------------------------------------ #
    langgraph_checkpoint_backend: Literal["memory", "sqlite", "postgres"] = Field(
        default="memory",
        description="Persistence backend for LangGraph conversation state",
    )

    # ------------------------------------------------------------------ #
    # Retrieval & Reranking
    # ------------------------------------------------------------------ #
    qdrant_top_k: int = Field(
        default=20,
        description="Number of candidate passages fetched from Qdrant",
    )
    cohere_rerank_top_n: int = Field(
        default=5,
        description="Top passages kept after Cohere reranking",
    )
    verification_max_retries: int = Field(
        default=2,
        description="Maximum Verification→Retrieval retry loops allowed",
    )

    # ------------------------------------------------------------------ #
    # Emergency / Safety
    # ------------------------------------------------------------------ #
    emergency_helpline_ncw: str = Field(
        default="7827170170",
        description="National Commission for Women 24/7 Helpline",
    )
    emergency_helpline_general: str = Field(
        default="112",
        description="General national emergency number",
    )
    dlsa_helpline: str = Field(
        default="15100",
        description="National Legal Services Authority helpline",
    )

    # ------------------------------------------------------------------ #
    # Edge-TTS Voice Configuration (10 Major Indian Languages)
    # ------------------------------------------------------------------ #
    tts_voice_english: str = Field(default="en-IN-NeerjaNeural")
    tts_voice_hindi: str = Field(default="hi-IN-SwaraNeural")
    tts_voice_kannada: str = Field(default="kn-IN-GaganNeural")
    tts_voice_telugu: str = Field(default="te-IN-ShrutiNeural")
    tts_voice_tamil: str = Field(default="ta-IN-PallaviNeural")
    tts_voice_bengali: str = Field(default="bn-IN-TanishaaNeural")
    tts_voice_marathi: str = Field(default="mr-IN-AarohiNeural")
    tts_voice_gujarati: str = Field(default="gu-IN-DhwaniNeural")
    tts_voice_malayalam: str = Field(default="ml-IN-SobhanaNeural")
    tts_voice_urdu: str = Field(default="ur-IN-GulNeural")

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def tts_voice_map(self) -> dict[str, str]:
        """Language code → Edge-TTS voice name mapping."""
        return {
            "en": self.tts_voice_english,
            "hi": self.tts_voice_hindi,
            "kn": self.tts_voice_kannada,
            "te": self.tts_voice_telugu,
            "ta": self.tts_voice_tamil,
            "bn": self.tts_voice_bengali,
            "mr": self.tts_voice_marathi,
            "gu": self.tts_voice_gujarati,
            "ml": self.tts_voice_malayalam,
            "ur": self.tts_voice_urdu,
        }

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns a cached singleton Settings instance.
    Use this function everywhere instead of instantiating Settings directly.
    """
    return Settings()
