"""
Agent Forge - Health Check Routes
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health", summary="System health check")
async def health_check():
    """Returns operational status and configuration summary."""
    return JSONResponse(
        content={
            "status": "healthy",
            "environment": settings.app_env,
            "gemini_model": settings.gemini_llm_model,
            "qdrant_collection": settings.qdrant_collection,
            "cohere_rerank_model": settings.cohere_rerank_model,
            "languages": ["en", "hi", "kn"],
            "emergency_contacts": {
                "ncw_helpline": settings.emergency_helpline_ncw,
                "emergency": settings.emergency_helpline_general,
                "dlsa": settings.dlsa_helpline,
            },
        }
    )
