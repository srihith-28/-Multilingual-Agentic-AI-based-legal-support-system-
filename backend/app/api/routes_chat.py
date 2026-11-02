"""
Agent Forge - Chat API Routes

Handles both text-based and voice-based legal queries.
Invokes the LangGraph multi-agent workflow and returns the structured response.
"""

import logging
import uuid
import asyncio
from typing import Optional
from urllib.parse import quote_plus

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.state import Language, InputMode

logger = logging.getLogger("agent_forge.api.chat")
router = APIRouter()
settings = get_settings()


# ------------------------------------------------------------------ #
# Request / Response Models
# ------------------------------------------------------------------ #

class ChatRequest(BaseModel):
    """Incoming chat message from the user."""
    message: str = Field(..., description="User's text query (or ASR-transcribed voice query)")
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for multi-turn conversation continuity. Auto-generated if not provided.",
    )
    language: Optional[str] = Field(
        default=None,
        description="Language hint: 'en', 'hi', or 'kn'. Auto-detected if not provided.",
    )
    input_mode: InputMode = Field(
        default=InputMode.TEXT,
        description="Whether this message originated from text or voice input.",
    )


class CitationItem(BaseModel):
    """A single legal citation in the response."""
    act_name: str
    section_number: str
    section_title: str
    content_excerpt: str
    full_text: Optional[str] = None
    source_url: Optional[str] = None
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Structured response from the Agent Forge legal system."""
    session_id: str
    plain_language_summary: str = Field(
        description="Layer 1: Plain-language legal guidance in the user's language"
    )
    statutory_citations: list[CitationItem] = Field(
        default_factory=list,
        description="Layer 2: Supporting statutory sections and citations",
    )
    disclaimer: str = "This information is for educational purposes only. Not legal advice."
    detected_language: str = "en"
    law_domain: str = "general_family_law"
    is_emergency: bool = False
    emergency_contacts: Optional[dict] = None
    needs_clarification: bool = False
    clarification_questions: list[str] = Field(default_factory=list)
    audio_available: bool = False
    audio_url: Optional[str] = None


# ------------------------------------------------------------------ #
# Helper: build ChatResponse from the dict returned by run_legal_agent
# ------------------------------------------------------------------ #

def _build_chat_response(result: dict, session_id: str) -> ChatResponse:
    """Converts the dict returned by run_legal_agent into a ChatResponse."""
    raw_citations = result.get("statutory_citations", [])

    citations = []
    for c in raw_citations:
        if isinstance(c, dict):
            act = c.get("act_name", "")
            sec = c.get("section_number", "")
            source = c.get("source_url")
            if not source and act:
                encoded = quote_plus(f"{act} Section {sec}")
                source = f"https://indiankanoon.org/search/?formInput={encoded}"

            citations.append(CitationItem(
                act_name=act,
                section_number=sec,
                section_title=c.get("section_title", ""),
                content_excerpt=c.get("content_excerpt", ""),
                full_text=c.get("full_text") or c.get("content_excerpt", ""),
                source_url=source,
                relevance_score=c.get("relevance_score"),
            ))

    return ChatResponse(
        session_id=session_id,
        plain_language_summary=result.get(
            "plain_language_summary",
            "I was unable to process your query. Please try again."
        ),
        statutory_citations=citations,
        disclaimer=result.get(
            "disclaimer",
            "This information is for educational purposes only. Not legal advice."
        ),
        detected_language=result.get("detected_language", "en"),
        law_domain=result.get("law_domain", "general_family_law"),
        is_emergency=result.get("is_emergency", False),
        emergency_contacts=result.get("emergency_contacts"),
        needs_clarification=result.get("needs_clarification", False),
        clarification_questions=result.get("clarification_questions", []),
        audio_available=False,
        audio_url=None,
    )


# ------------------------------------------------------------------ #
# Routes
# ------------------------------------------------------------------ #

@router.post("/chat/stream", summary="Send a legal query (Server-Sent Events streaming)")
async def chat_stream(request: ChatRequest):
    """
    Streaming SSE variant of the chat endpoint.

    Streams the plain-language response text in real-time chunks while the
    LangGraph pipeline runs. Sends a final 'complete' event with full metadata
    (citations, domain, is_emergency, etc.).

    SSE Event types:
      data: {"type": "chunk",    "text": "...partial text..."}
      data: {"type": "complete", "data": { <full ChatResponse JSON> }}
      data: {"type": "error",    "message": "..."}
      data: [DONE]
    """
    import json

    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"[{session_id}] Streaming query: '{request.message[:80]}'")

    async def event_generator():
        try:
            from app.graph import run_legal_agent

            # Immediate status event to initiate stream transmission
            yield ": connected\n\n"

            # Run agent as a task so we can stream keep-alive pings during execution
            agent_task = asyncio.create_task(
                run_legal_agent(
                    user_query=request.message,
                    session_id=session_id,
                    language_hint=request.language,
                    input_mode=request.input_mode.value if hasattr(request.input_mode, 'value') else request.input_mode,
                )
            )

            # Send periodic keep-alive comments so browser/proxy never times out
            while not agent_task.done():
                await asyncio.sleep(2.5)
                if not agent_task.done():
                    yield ": keep-alive\n\n"

            result = await agent_task

            # result is a dict — build the response object
            response_obj = _build_chat_response(result, session_id)

            # Stream the plain-language summary word-by-word for effect
            summary = response_obj.plain_language_summary or ""
            words = summary.split(" ")
            chunk_size = 4  # words per SSE event

            for i in range(0, len(words), chunk_size):
                chunk_words = words[i : i + chunk_size]
                chunk_text = " ".join(chunk_words)
                if i + chunk_size < len(words):
                    chunk_text += " "
                event = json.dumps({"type": "chunk", "text": chunk_text})
                yield f"data: {event}\n\n"
                await asyncio.sleep(0.01)

            # Send complete event with full response metadata
            complete_data = response_obj.model_dump()
            complete_event = json.dumps({"type": "complete", "data": complete_data})
            yield f"data: {complete_event}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.exception(f"[{session_id}] Streaming error: {e}")
            error_event = json.dumps({"type": "error", "message": f"{type(e).__name__}: {str(e)}"})
            yield f"data: {error_event}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/chat", response_model=ChatResponse, summary="Send a legal query")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Main conversational endpoint.

    Accepts a text (or pre-transcribed voice) query and runs it through
    the complete LangGraph multi-agent pipeline:
    1. Language Detection
    2. Safety / Emergency Fast-Path
    3. Intent Agent → Context Agent → Planner Agent
    4. Retrieval Agent → Hybrid RAG → Cohere Reranker
    5. Reasoning Agent → Verification Agent (with retry loop)
    6. Response Agent → Two-layer response

    Returns structured legal guidance with statutory citations in the user's language.
    """
    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"[{session_id}] Received query: '{request.message[:80]}...'")

    try:
        from app.graph import run_legal_agent

        result = await run_legal_agent(
            user_query=request.message,
            session_id=session_id,
            language_hint=request.language,
            input_mode=request.input_mode.value if hasattr(request.input_mode, 'value') else request.input_mode,
        )

        return _build_chat_response(result, session_id)

    except ImportError as e:
        logger.error(f"[{session_id}] Import error (dependency missing?): {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Agent system not yet fully initialized. Missing dependency: {e}",
        )
    except Exception as e:
        logger.exception(f"[{session_id}] Unhandled error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent error ({type(e).__name__}): {str(e)}",
        )
