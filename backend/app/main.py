"""
Agent Forge - FastAPI Application Entry Point

Multilingual Agentic AI Family Law Information and Decision-Support System
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.api.routes_chat import router as chat_router
from app.api.routes_audio import router as audio_router
from app.api.routes_health import router as health_router

# ------------------------------------------------------------------ #
# Logging
# ------------------------------------------------------------------ #
settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("agent_forge")


# ------------------------------------------------------------------ #
# Application Lifespan (startup / shutdown)
# ------------------------------------------------------------------ #
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Initializes Qdrant client and Gemini connections on startup.
    """
    logger.info("🚀 Agent Forge starting up...")
    logger.info(f"   Environment : {settings.app_env}")
    logger.info(f"   Gemini Model: {settings.gemini_llm_model}")
    logger.info(f"   Qdrant      : {settings.qdrant_url}")

    # Lazy-import to verify critical dependencies are installed
    try:
        import google.genai  # noqa: F401
        logger.info("   ✅ Google Gemini SDK loaded")
    except ImportError:
        logger.error("   ❌ google-genai not installed. Run: pip install google-genai")

    try:
        from qdrant_client import QdrantClient  # noqa: F401
        logger.info("   ✅ Qdrant client loaded")
    except ImportError:
        logger.error("   ❌ qdrant-client not installed. Run: pip install qdrant-client")

    try:
        import cohere  # noqa: F401
        logger.info("   ✅ Cohere SDK loaded")
    except ImportError:
        logger.error("   ❌ cohere not installed. Run: pip install cohere")

    try:
        import edge_tts  # noqa: F401
        logger.info("   ✅ Edge-TTS loaded")
    except ImportError:
        logger.warning("   ⚠️  edge-tts not installed. Voice output will be disabled.")

    logger.info("✅ Agent Forge is ready.")
    yield

    logger.info("🛑 Agent Forge shutting down...")


# ------------------------------------------------------------------ #
# FastAPI Application
# ------------------------------------------------------------------ #
app = FastAPI(
    title="Agent Forge — Multilingual Legal Support System",
    description=(
        "An Agentic AI system for Indian Family Law information and decision-support. "
        "Supports English, Hindi, and Kannada via voice and text interactions."
    ),
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# ------------------------------------------------------------------ #
# CORS Middleware
# ------------------------------------------------------------------ #
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ #
# Routers (Supporting both /api and /api/v1)
# ------------------------------------------------------------------ #
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(chat_router,   prefix="/api", tags=["Chat"])
app.include_router(audio_router,  prefix="/api", tags=["Audio"])

app.include_router(health_router, prefix="/api/v1", tags=["Health-v1"])
app.include_router(chat_router,   prefix="/api/v1", tags=["Chat-v1"])
app.include_router(audio_router,  prefix="/api/v1", tags=["Audio-v1"])


# ------------------------------------------------------------------ #
# API Info Endpoint
# ------------------------------------------------------------------ #
@app.get("/api/info", tags=["Root"])
async def api_info():
    return JSONResponse(
        content={
            "system": "Agent Forge — Multilingual Agentic AI Legal Support System",
            "version": "1.0.0",
            "languages_supported": [
                "English",
                "Hindi (हिन्दी)",
                "Kannada (ಕನ್ನಡ)",
                "Telugu (తెలుగు)",
                "Tamil (தமிழ்)",
                "Bengali (বাংলা)",
                "Marathi (मराठी)",
                "Gujarati (ગુજરાતી)",
                "Malayalam (മലയാളം)",
                "Urdu (اردو)",
            ],
            "domains": [
                "Divorce & Separation",
                "Maintenance & Alimony",
                "Domestic Violence Protection",
                "Child Custody & Guardianship",
                "Restitution of Conjugal Rights",
            ],
            "docs": "/docs",
            "status": "operational",
        }
    )


# ------------------------------------------------------------------ #
# Frontend Static Mount (Standalone Production Serving)
# ------------------------------------------------------------------ #
from pathlib import Path
_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
else:
    @app.get("/", tags=["Root"])
    async def root():
        return await api_info()


# ------------------------------------------------------------------ #
# Entrypoint
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.effective_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
