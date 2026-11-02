"""
Agent Forge - TTS Service (Text-to-Speech)

Converts legal response text to natural-sounding speech using
Microsoft Edge-TTS neural voices.

Supported voices (10 Indian Languages):
  - English   : en-IN-NeerjaNeural (Female) / en-IN-PrabhatNeural (Male)
  - Hindi     : hi-IN-SwaraNeural (Female) / hi-IN-MadhurNeural (Male)
  - Kannada   : kn-IN-SapnaNeural (Female) / kn-IN-GaganNeural (Male)
  - Telugu    : te-IN-ShrutiNeural (Female) / te-IN-MohanNeural (Male)
  - Tamil     : ta-IN-PallaviNeural (Female) / ta-IN-ValluvarNeural (Male)
  - Bengali   : bn-IN-TanishaaNeural (Female) / bn-IN-BashkarNeural (Male)
  - Marathi   : mr-IN-AarohiNeural (Female) / mr-IN-ManoharNeural (Male)
  - Gujarati  : gu-IN-DhwaniNeural (Female) / gu-IN-NiranjanNeural (Male)
  - Malayalam : ml-IN-SobhanaNeural (Female) / ml-IN-MidhunNeural (Male)
  - Urdu      : ur-IN-GulNeural (Female) / ur-IN-SalmanNeural (Male)

Edge-TTS advantages:
  - Zero API cost (Microsoft Azure neural TTS, freely accessible).
  - Native pronunciation of Indian names, legal terms, and regional terminology.
  - Natural prosody for long legal text with proper sentence-level pauses.
  - Async output streaming (low latency).
"""

import logging
import asyncio
import os
import re
import tempfile
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger("agent_forge.speech.tts")
settings = get_settings()


# ------------------------------------------------------------------ #
# Legal Text Pre-Processor
# ------------------------------------------------------------------ #

def _preprocess_for_tts(text: str, language: str) -> str:
    """
    Cleans and prepares legal text for natural-sounding TTS synthesis.

    - Removes markdown formatting (bold, italics, headers).
    - Expands common legal abbreviations to full spoken forms.
    - Normalizes section number pronunciation.
    """
    # Extract link text from markdown links: [link text](url) -> link text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove all bracketed / parenthetical text: (...), [...], {...}, （...）
    text = re.sub(r'\([^)]*\)|\[[^\]]*\]|\{[^}]*\}|（[^）]*）', '', text)

    # Remove markdown bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s+', '', text)

    # Clean up whitespace before punctuation marks caused by bracket removal
    text = re.sub(r'\s+([,.\?!;:])', r'\1', text)

    # Expand common abbreviations for clearer TTS pronunciation
    abbreviations = {
        "HMA": "Hindu Marriage Act",
        "SMA": "Special Marriage Act",
        "PWDVA": "Protection of Women from Domestic Violence Act",
        "BNSS": "Bharatiya Nagarik Suraksha Sanhita",
        "CrPC": "Code of Criminal Procedure",
        "HMGA": "Hindu Minority and Guardianship Act",
        "HSA": "Hindu Succession Act",
        "DLSA": "District Legal Services Authority",
        "NCW": "National Commission for Women",
        "§": "Section ",
        "Sec.": "Section",
    }
    for abbr, full in abbreviations.items():
        text = text.replace(abbr, full)

    # Convert 'AI' / 'AI-' to native phonetic script in Indian languages so neural voices pronounce it accurately without skipping
    ai_phonetics = {
        "te": "ఏఐ",
        "kn": "ಎಐ",
        "hi": "एआई",
        "ta": "ஏஐ",
        "bn": "এআই",
        "mr": "एआय",
        "gu": "એઆઈ",
        "ml": "എഐ",
        "ur": "اے آئی",
    }
    target_ai = ai_phonetics.get(language)
    if target_ai:
        text = re.sub(r'\bA\.?I\.?[-–—]\s*', f"{target_ai} ", text, flags=re.IGNORECASE)
        text = re.sub(r'\bA\.?I\.?\b', target_ai, text, flags=re.IGNORECASE)
    else:
        text = re.sub(r'\bA\.?I\.?[-–—]\s*', 'AI ', text, flags=re.IGNORECASE)

    # Remove emojis (they cause TTS issues)
    text = re.sub(r'[\U0001F000-\U0001FFFF]', '', text)

    # Normalize multiple newlines → single pause
    text = re.sub(r'\n{2,}', '. ', text)
    text = re.sub(r'\n', ', ', text)

    # Limit to 5000 chars to avoid TTS timeouts (split for longer text)
    return text[:5000].strip()


# ------------------------------------------------------------------ #
# Core TTS Function
# ------------------------------------------------------------------ #

async def synthesize_text(
    text: str,
    voice: str,
    output_path: str,
    rate: str = "+0%",
    volume: str = "+0%",
) -> str:
    """
    Synthesizes speech from text using Edge-TTS and saves to an MP3 file.

    Args:
        text        : Text to synthesize (will be cleaned for TTS).
        voice       : Edge-TTS voice name (e.g., 'hi-IN-SwaraNeural').
        output_path : Full path to save the output MP3 file.
        rate        : Speech rate adjustment (e.g., '-10%' to slow down).
        volume      : Volume adjustment (e.g., '+10%' to increase).

    Returns:
        The output_path where the audio was saved.
    """
    # If voice is English but text contains Indian script, auto-route to the native voice
    from app.speech.asr_service import detect_script
    script = detect_script(text)
    if script != "en" and "en-in" in voice.lower():
        fallback_voices = {
            "te": getattr(settings, "tts_voice_telugu", "te-IN-ShrutiNeural"),
            "kn": getattr(settings, "tts_voice_kannada", "kn-IN-GaganNeural"),
            "hi": getattr(settings, "tts_voice_hindi", "hi-IN-SwaraNeural"),
            "ta": getattr(settings, "tts_voice_tamil", "ta-IN-PallaviNeural"),
            "bn": getattr(settings, "tts_voice_bengali", "bn-IN-TanishaaNeural"),
            "mr": getattr(settings, "tts_voice_marathi", "mr-IN-AarohiNeural"),
            "gu": getattr(settings, "tts_voice_gujarati", "gu-IN-DhwaniNeural"),
            "ml": getattr(settings, "tts_voice_malayalam", "ml-IN-SobhanaNeural"),
            "ur": getattr(settings, "tts_voice_urdu", "ur-IN-GulNeural"),
        }
        if script in fallback_voices:
            voice = fallback_voices[script]
            logger.info(f"[TTS] Auto-routed to {voice} based on text script '{script}'")

    # Determine language from voice name for preprocessing
    lang = "en"
    for code in ("hi", "kn", "te", "ta", "bn", "mr", "gu", "ml", "ur", "en"):
        if f"{code}-IN" in voice.lower():
            lang = code
            break

    clean_text = _preprocess_for_tts(text, lang)

    if not clean_text:
        raise ValueError("Text is empty after preprocessing. Cannot synthesize audio.")

    logger.info(
        f"[TTS] Synthesizing | Voice: {voice} | "
        f"Text length: {len(clean_text)} chars | Output: {os.path.basename(output_path)}"
    )

    import edge_tts

    communicate = edge_tts.Communicate(
        text=clean_text,
        voice=voice,
        rate=rate,
        volume=volume,
    )

    await communicate.save(output_path)

    file_size_kb = os.path.getsize(output_path) / 1024
    logger.info(f"[TTS] Audio saved: {output_path} ({file_size_kb:.1f} KB)")

    return output_path


# ------------------------------------------------------------------ #
# Convenience Wrappers
# ------------------------------------------------------------------ #

async def synthesize_in_language(
    text: str,
    language: str,
    output_path: Optional[str] = None,
    gender: str = "female",
) -> str:
    """
    Synthesizes text in the specified language using the appropriate neural voice.

    Args:
        text        : Text to synthesize.
        language    : Language code ('en', 'hi', 'kn', 'te', 'ta', 'bn', 'mr', 'gu', 'ml', 'ur').
        output_path : Output file path. Auto-generated if not provided.
        gender      : 'female' (default) or 'male' voice preference.

    Returns:
        Path to the synthesized audio file.
    """
    voice_map = {
        "en": {
            "female": getattr(settings, "tts_voice_english", "en-IN-NeerjaNeural"),
            "male":   "en-IN-PrabhatNeural",
        },
        "hi": {
            "female": getattr(settings, "tts_voice_hindi", "hi-IN-SwaraNeural"),
            "male":   "hi-IN-MadhurNeural",
        },
        "kn": {
            "female": "kn-IN-SapnaNeural",
            "male":   getattr(settings, "tts_voice_kannada", "kn-IN-GaganNeural"),
        },
        "te": {
            "female": getattr(settings, "tts_voice_telugu", "te-IN-ShrutiNeural"),
            "male":   "te-IN-MohanNeural",
        },
        "ta": {
            "female": getattr(settings, "tts_voice_tamil", "ta-IN-PallaviNeural"),
            "male":   "ta-IN-ValluvarNeural",
        },
        "bn": {
            "female": getattr(settings, "tts_voice_bengali", "bn-IN-TanishaaNeural"),
            "male":   "bn-IN-BashkarNeural",
        },
        "mr": {
            "female": getattr(settings, "tts_voice_marathi", "mr-IN-AarohiNeural"),
            "male":   "mr-IN-ManoharNeural",
        },
        "gu": {
            "female": getattr(settings, "tts_voice_gujarati", "gu-IN-DhwaniNeural"),
            "male":   "gu-IN-NiranjanNeural",
        },
        "ml": {
            "female": getattr(settings, "tts_voice_malayalam", "ml-IN-SobhanaNeural"),
            "male":   "ml-IN-MidhunNeural",
        },
        "ur": {
            "female": getattr(settings, "tts_voice_urdu", "ur-IN-GulNeural"),
            "male":   "ur-IN-SalmanNeural",
        },
    }

    lang_voices = voice_map.get(language, voice_map["en"])
    voice = lang_voices.get(gender, lang_voices["female"])

    if output_path is None:
        import uuid
        output_dir = os.path.join(tempfile.gettempdir(), "agent_forge_audio")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"tts_{uuid.uuid4().hex}.mp3")

    return await synthesize_text(text=text, voice=voice, output_path=output_path)


async def list_available_voices() -> list[dict]:
    """Returns all available Edge-TTS voices for supported Indian languages."""
    import edge_tts

    all_voices = await edge_tts.list_voices()
    indian_voices = []
    for v in all_voices:
        loc = v.get("Locale", "")
        if "-IN" in loc:
            code = loc.split("-")[0].lower()
            indian_voices.append({
                "name": v["Name"],
                "locale": loc,
                "gender": v["Gender"],
                "language": code if code in ("en", "hi", "kn", "te", "ta", "bn", "mr", "gu", "ml", "ur") else "other",
            })
    return indian_voices
