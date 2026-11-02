"""
Agent Forge - Audio Routes

Handles:
1. POST /audio/transcribe   → Voice-to-text (ASR) in English, Hindi, or Kannada
2. POST /audio/synthesize   → Text-to-voice (TTS) using Edge-TTS neural voices
3. GET  /audio/voices       → List available multilingual TTS voices
"""

import logging
import uuid
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.core.config import get_settings

logger = logging.getLogger("agent_forge.api.audio")
router = APIRouter()
settings = get_settings()

# Temporary audio output directory
AUDIO_OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "agent_forge_audio")
os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)


def _cleanup_temp_file(path: str):
    """Background task: removes a temporary audio file after it's been served."""
    try:
        import time
        time.sleep(2)  # Brief delay to ensure FileResponse finishes streaming
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass  # Non-critical — OS temp cleanup will eventually handle it


# ------------------------------------------------------------------ #
# Request / Response Models
# ------------------------------------------------------------------ #

class TranscriptionResponse(BaseModel):
    """Result of speech-to-text transcription."""
    transcript: str
    detected_language: str
    confidence: Optional[float] = None
    duration_seconds: Optional[float] = None


class SynthesisRequest(BaseModel):
    """Request for text-to-speech synthesis."""
    text: str = Field(..., description="Text to synthesize into speech")
    language: str = Field(
        default="en",
        description="Language code ('en', 'hi', 'kn', 'te', 'ta', 'bn', 'mr', 'gu', 'ml', 'ur')",
    )
    voice_override: Optional[str] = Field(
        default=None,
        description="Override the default Edge-TTS voice name (e.g. 'te-IN-ShrutiNeural')",
    )


# ------------------------------------------------------------------ #
# Routes
# ------------------------------------------------------------------ #

@router.post(
    "/audio/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe voice audio to text (ASR)",
)
async def transcribe_audio(
    audio: UploadFile = File(..., alias="audio", description="Audio file (WAV, WebM, MP3, M4A)"),
    language_hint: Optional[str] = Form(
        default=None,
        description="Optional language hint: 'en', 'hi', 'kn', 'te', 'ta', 'bn', 'mr', 'gu', 'ml', 'ur'",
    ),
):
    """
    Accepts an uploaded audio file and returns the transcribed text
    along with the detected language.

    Supported formats: WAV, WebM, MP3, M4A, OGG.
    Uses Gemini Multimodal Audio for multilingual transcription including code-mixed
    Hindi-English (Hinglish) and Kannada-English (Kanglish).
    """
    from app.speech.asr_service import transcribe_audio_file

    # Validate file type
    allowed_types = {"audio/wav", "audio/webm", "audio/mpeg", "audio/mp4", "audio/ogg", "audio/x-wav", "audio/flac"}
    content_base = (audio.content_type or "").split(";")[0].strip()
    if content_base and content_base not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio format: {audio.content_type}. Supported: WAV, WebM, MP3, M4A, OGG, FLAC",
        )

    # Save to temp file
    suffix = os.path.splitext(audio.filename or "audio.webm")[1] or ".webm"
    tmp_path = os.path.join(AUDIO_OUTPUT_DIR, f"input_{uuid.uuid4().hex}{suffix}")

    try:
        content = await audio.read()
        with open(tmp_path, "wb") as f:
            f.write(content)

        result = await transcribe_audio_file(tmp_path, language_hint=language_hint)
        return result

    except Exception as e:
        logger.exception(f"ASR transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post(
    "/audio/synthesize",
    summary="Convert text to multilingual speech (TTS)",
)
async def synthesize_speech(request: SynthesisRequest, background_tasks: BackgroundTasks):
    """
    Converts text to natural-sounding speech using Microsoft Edge-TTS neural voices.

    Supported languages and default voices:
    - English  : en-IN-NeerjaNeural
    - Hindi    : hi-IN-SwaraNeural
    - Kannada  : kn-IN-GaganNeural

    Returns the synthesized audio as an MP3 file.
    """
    from app.speech.tts_service import synthesize_text
    from app.speech.asr_service import detect_script

    output_path = os.path.join(AUDIO_OUTPUT_DIR, f"tts_{uuid.uuid4().hex}.mp3")

    try:
        req_lang = request.language
        script_lang = detect_script(request.text)
        if script_lang != "en" and req_lang in ("en", None, ""):
            req_lang = script_lang

        voice = request.voice_override or settings.tts_voice_map.get(req_lang, settings.tts_voice_english)
        await synthesize_text(text=request.text, voice=voice, output_path=output_path)

        # Schedule cleanup of the temp audio file after the response is sent
        background_tasks.add_task(_cleanup_temp_file, output_path)

        return FileResponse(
            path=output_path,
            media_type="audio/mpeg",
            filename="response.mp3",
            headers={"X-Language": request.language, "X-Voice": voice},
        )

    except Exception as e:
        logger.exception(f"TTS synthesis failed: {e}")
        # Clean up on error too
        if os.path.exists(output_path):
            os.remove(output_path)
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")


@router.get("/audio/voices", summary="List available TTS voices")
async def list_voices():
    """Returns the available Edge-TTS voices for each supported language."""
    return JSONResponse(
        content={
            "voices": {
                "en": [
                    {"name": "en-IN-NeerjaNeural", "gender": "Female", "locale": "en-IN"},
                    {"name": "en-IN-PrabhatNeural", "gender": "Male", "locale": "en-IN"},
                ],
                "hi": [
                    {"name": "hi-IN-SwaraNeural", "gender": "Female", "locale": "hi-IN"},
                    {"name": "hi-IN-MadhurNeural", "gender": "Male", "locale": "hi-IN"},
                ],
                "kn": [
                    {"name": "kn-IN-SapnaNeural", "gender": "Female", "locale": "kn-IN"},
                    {"name": "kn-IN-GaganNeural", "gender": "Male", "locale": "kn-IN"},
                ],
                "te": [
                    {"name": "te-IN-ShrutiNeural", "gender": "Female", "locale": "te-IN"},
                    {"name": "te-IN-MohanNeural", "gender": "Male", "locale": "te-IN"},
                ],
                "ta": [
                    {"name": "ta-IN-PallaviNeural", "gender": "Female", "locale": "ta-IN"},
                    {"name": "ta-IN-ValluvarNeural", "gender": "Male", "locale": "ta-IN"},
                ],
                "bn": [
                    {"name": "bn-IN-TanishaaNeural", "gender": "Female", "locale": "bn-IN"},
                    {"name": "bn-IN-BashkarNeural", "gender": "Male", "locale": "bn-IN"},
                ],
                "mr": [
                    {"name": "mr-IN-AarohiNeural", "gender": "Female", "locale": "mr-IN"},
                    {"name": "mr-IN-ManoharNeural", "gender": "Male", "locale": "mr-IN"},
                ],
                "gu": [
                    {"name": "gu-IN-DhwaniNeural", "gender": "Female", "locale": "gu-IN"},
                    {"name": "gu-IN-NiranjanNeural", "gender": "Male", "locale": "gu-IN"},
                ],
                "ml": [
                    {"name": "ml-IN-SobhanaNeural", "gender": "Female", "locale": "ml-IN"},
                    {"name": "ml-IN-MidhunNeural", "gender": "Male", "locale": "ml-IN"},
                ],
                "ur": [
                    {"name": "ur-IN-GulNeural", "gender": "Female", "locale": "ur-IN"},
                    {"name": "ur-IN-SalmanNeural", "gender": "Male", "locale": "ur-IN"},
                ],
            }
        }
    )
