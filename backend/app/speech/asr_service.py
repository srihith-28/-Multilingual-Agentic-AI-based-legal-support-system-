"""
Agent Forge - ASR Service (Speech-to-Text)

Provides multilingual voice transcription using:
  - Primary  : Google Gemini Multimodal Audio (handles Hindi, Kannada, English, code-mixed)
  - Fallback : Language detection via langdetect on text queries

Supports: English (en), Hindi (hi), Kannada (kn)
Also handles code-mixed inputs: Hinglish, Kanglish, Kannada-English.
"""

import logging
import asyncio
import os
from typing import Optional

from app.core.config import get_settings
from app.core.state import Language

logger = logging.getLogger("agent_forge.speech.asr")
settings = get_settings()


# ------------------------------------------------------------------ #
# Language Detection (for text queries)
# ------------------------------------------------------------------ #

SUPPORTED_LANGUAGES = ("en", "hi", "kn", "te", "ta", "bn", "mr", "gu", "ml", "ur")


def detect_script(text: str) -> str:
    """
    Detects the Indian script used in the text via Unicode block ranges.
    This is instantaneous and 100% deterministic for native Indian scripts.
    """
    for ch in text:
        cp = ord(ch)
        if 0x0C00 <= cp <= 0x0C7F:
            return "te"  # Telugu
        if 0x0C80 <= cp <= 0x0CFF:
            return "kn"  # Kannada
        if 0x0B80 <= cp <= 0x0BFF:
            return "ta"  # Tamil
        if 0x0980 <= cp <= 0x09FF:
            return "bn"  # Bengali
        if 0x0A80 <= cp <= 0x0AFF:
            return "gu"  # Gujarati
        if 0x0D00 <= cp <= 0x0D7F:
            return "ml"  # Malayalam
        if 0x0600 <= cp <= 0x06FF:
            return "ur"  # Urdu / Arabic
        if 0x0900 <= cp <= 0x097F:
            return "hi"  # Devanagari (Hindi / Marathi)
    return "en"


async def detect_language(text: str, hint: Optional[str] = None) -> Language:
    """
    Detects the language of a text string.
    Returns a Language enum value.

    Args:
        text : Text to detect language from.
        hint : Optional user-provided language hint.
    """
    hint_str = hint.value if hasattr(hint, "value") else str(hint) if hint else ""

    # 1. Deterministic native script check (fastest and 100% accurate for Indian scripts)
    script_lang = detect_script(text)
    if script_lang != "en":
        # Devanagari is shared between Hindi and Marathi
        if script_lang == "hi" and hint_str == "mr":
            return Language.MARATHI
        return Language(script_lang)

    # 2. If user selected a specific language (e.g. from the UI dropdown), respect it
    if hint_str and hint_str in SUPPORTED_LANGUAGES and hint_str != "en":
        return Language(hint_str)

    # 3. Try Gemini-based language detection (most accurate for Romanized Indian text like Hinglish/Telugish)
    try:
        detected = await _detect_with_gemini(text)
        return detected
    except Exception:
        pass

    # 4. Fallback: langdetect (library-based)
    try:
        return await asyncio.to_thread(_detect_with_langdetect, text)
    except Exception as e:
        logger.warning(f"[ASR] Language detection failed: {e}. Defaulting to English.")
        return Language.ENGLISH


async def _detect_with_gemini(text: str) -> Language:
    """Uses Gemini to detect language — most accurate for Indian scripts."""
    import google.genai as genai
    from google.genai import types as genai_types

    client = genai.Client(api_key=settings.gemini_api_key)

    prompt = (
        f'Detect the primary language of this Indian citizen text. '
        f'Reply with ONLY one of these codes: en, hi, kn, te, ta, bn, mr, gu, ml, ur\n\n'
        f'Text: "{text[:300]}"'
    )

    response = client.models.generate_content(
        model=settings.gemini_llm_model,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=5,
        ),
    )
    code = response.text.strip().lower()[:2]
    return Language(code) if code in SUPPORTED_LANGUAGES else Language.ENGLISH


def _detect_with_langdetect(text: str) -> Language:
    """Fallback language detection using the langdetect library."""
    from langdetect import detect, LangDetectException

    try:
        code = detect(text)
        # Map langdetect codes to our Language enum
        mapping = {
            "en": Language.ENGLISH,
            "hi": Language.HINDI,
            "kn": Language.KANNADA,
            "te": Language.TELUGU,
            "ta": Language.TAMIL,
            "bn": Language.BENGALI,
            "mr": Language.MARATHI,
            "gu": Language.GUJARATI,
            "ml": Language.MALAYALAM,
            "ur": Language.URDU,
        }
        return mapping.get(code, Language.ENGLISH)
    except LangDetectException:
        return Language.ENGLISH


# ------------------------------------------------------------------ #
# Voice Transcription (ASR)
# ------------------------------------------------------------------ #

async def transcribe_audio_file(
    audio_path: str,
    language_hint: Optional[str] = None,
) -> dict:
    """
    Transcribes an audio file to text using Gemini Multimodal Audio.

    Args:
        audio_path    : Absolute path to the audio file (WAV, WebM, MP3, M4A).
        language_hint : Optional language code.

    Returns:
        Dict with keys: transcript, detected_language, confidence, duration_seconds
    """
    logger.info(f"[ASR] Transcribing: {os.path.basename(audio_path)}")

    try:
        result = await _transcribe_with_gemini(audio_path, language_hint)
        return result
    except Exception as e:
        logger.error(f"[ASR] Gemini transcription failed: {e}")
        raise RuntimeError(f"Audio transcription failed: {e}")


async def _transcribe_with_gemini(audio_path: str, language_hint: Optional[str]) -> dict:
    """
    Transcribes audio using Gemini's multimodal capabilities.
    Gemini natively understands Indian languages and code-mixed speech.
    """
    import base64
    import google.genai as genai
    from google.genai import types as genai_types

    client = genai.Client(api_key=settings.gemini_api_key)

    # Determine MIME type from file extension
    ext = os.path.splitext(audio_path)[1].lower()
    mime_map = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".webm": "audio/webm",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
    }
    mime_type = mime_map.get(ext, "audio/wav")

    lang_names = {
        "en": "English", "hi": "Hindi", "kn": "Kannada",
        "te": "Telugu", "ta": "Tamil", "bn": "Bengali",
        "mr": "Marathi", "gu": "Gujarati", "ml": "Malayalam", "ur": "Urdu"
    }

    lang_instruction = ""
    if language_hint:
        lang_instruction = f"The speaker is primarily using {lang_names.get(language_hint, 'English')}."

    prompt = (
        f"Transcribe this audio recording accurately. "
        f"{lang_instruction} "
        f"The audio may contain Indian languages (English, Hindi, Kannada, Telugu, Tamil, Bengali, Marathi, Gujarati, Malayalam, Urdu) or code-mixed vernacular speech. "
        f"Preserve all words exactly as spoken. Do not translate — transcribe verbatim. "
        f"Return ONLY the transcript text."
    )

    def _run_transcription():
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # Use the google-genai SDK's proper Part type for inline data
        audio_part = genai_types.Part.from_bytes(
            data=audio_bytes,
            mime_type=mime_type,
        )

        response = client.models.generate_content(
            model=settings.gemini_llm_model,
            contents=[audio_part, prompt],
        )
        return response.text.strip()

    transcript = await asyncio.to_thread(_run_transcription)

    # Detect language of the transcription
    detected_lang = await detect_language(transcript, hint=language_hint)

    logger.info(
        f"[ASR] Transcribed ({detected_lang.value}): '{transcript[:80]}...'"
    )

    return {
        "transcript": transcript,
        "detected_language": detected_lang.value,
        "confidence": None,  # Gemini does not expose confidence scores directly
        "duration_seconds": None,
    }
