"""
Agent Forge - Response Agent

Formats the verified reasoning draft into the final two-layer response:
- Layer 1: Plain-language, compassionate citizen-facing explanation
  in the user's detected language (English, Hindi, or Kannada).
- Layer 2: Statutory citation drawer with exact Acts, Section numbers,
  and official source references.

Also handles:
- Clarification branch formatting (when needs_clarification=True).
- Emergency response passthrough formatting.
- Safe legal aid advisory when max retries are exhausted.
- Multilingual disclaimer formatting.

Outputs:
    - final_response : ResponseLayer Pydantic object
"""

import logging
import urllib.parse
from pydantic import BaseModel, Field
import google.genai as genai
from google.genai import types

from app.core.config import get_settings
from app.core.state import (
    LegalAgentState,
    ResponseLayer,
    Language,
    VerificationStatus,
)

logger = logging.getLogger("agent_forge.agents.response")
settings = get_settings()


# ------------------------------------------------------------------ #
# Disclaimers (multilingual)
# ------------------------------------------------------------------ #

DISCLAIMERS = {
    "en": (
        "⚖️ This information is for educational and decision-support purposes only. "
        "It does not constitute legal advice. For personalized legal counsel, please consult "
        "a qualified family law advocate or visit your nearest District Legal Services Authority (DLSA) "
        f"for FREE legal aid (Helpline: {settings.dlsa_helpline})."
    ),
    "hi": (
        "⚖️ यह जानकारी केवल शैक्षिक और निर्णय-सहायता उद्देश्यों के लिए है। "
        "यह कानूनी सलाह नहीं है। व्यक्तिगत कानूनी परामर्श के लिए, कृपया एक योग्य "
        "पारिवारिक कानून वकील से परामर्श करें या अपने निकटतम जिला कानूनी सेवा प्राधिकरण (DLSA) "
        f"में जाएं — मुफ्त कानूनी सहायता के लिए (हेल्पलाइन: {settings.dlsa_helpline})।"
    ),
    "kn": (
        "⚖️ ಈ ಮಾಹಿತಿಯು ಕೇವಲ ಶೈಕ್ಷಣಿಕ ಮತ್ತು ನಿರ್ಧಾರ-ಸಹಾಯ ಉದ್ದೇಶಗಳಿಗಾಗಿ ಮಾತ್ರ. "
        "ಇದು ಕಾನೂನು ಸಲಹೆ ಅಲ್ಲ. ವ್ಯಕ್ತಿಗತ ಕಾನೂನು ಸಲಹೆಗಾಗಿ, ದಯವಿಟ್ಟು ಅರ್ಹ "
        "ಕೌಟುಂಬಿಕ ಕಾನೂನು ವಕೀಲರನ್ನು ಸಂಪರ್ಕಿಸಿ ಅಥವಾ ನಿಮ್ಮ ಹತ್ತಿರದ "
        f"ಜಿಲ್ಲಾ ಕಾನೂನು ಸೇವಾ ಪ್ರಾಧಿಕಾರ (DLSA) ಗೆ ಭೇಟಿ ನೀಡಿ (ಸಹಾಯವಾಣಿ: {settings.dlsa_helpline})."
    ),
    "te": (
        "⚖️ ఈ సమాచారం కేవలం విద్యా మరియు నిర్ణయ-సహాయ ప్రయోజనాల కోసం మాత్రమే. "
        "ఇది చట్టపరమైన సలహా కాదు. వ్యక్తిగత చట్టపరమైన సహాయం కోసం, దయచేసి అర్హత కలిగిన "
        "ఫ్యామిలీ లా న్యాయవాదిని సంప్రదించండి లేదా ఉచిత న్యాయ సహాయం కోసం సమీపంలోని "
        f"జిల్లా న్యాయ సేవల అధికార సంస్థ (DLSA) ను సంప్రదించండి (హెల్ప్‌లైన్: {settings.dlsa_helpline})."
    ),
    "ta": (
        "⚖️ இந்தத் தகவல் கல்வி மற்றும் முடிவெடுக்கும் நோக்கங்களுக்காக மட்டுமே. "
        "இது சட்ட ஆலோசனையாகாது. தனிப்பயனாக்கப்பட்ட சட்ட ஆலோசனைக்கு, தயவுசெய்து தகுதியான "
        "குடும்ப நல வழக்கறிஞரை அணுகவும் அல்லது இலவச சட்ட உதவிக்கு உங்கள் அருகிலுள்ள "
        f"மாவட்ட சட்ட சேவைகள் ஆணையத்தை (DLSA) தொடர்பு கொள்ளவும் (உதவி எண்: {settings.dlsa_helpline})."
    ),
    "bn": (
        "⚖️ এই তথ্য শুধুমাত্র শিক্ষামূলক এবং সিদ্ধান্ত-সহায়তা উদ্দেশ্যে। "
        "এটি আইনি পরামর্শ নয়। ব্যক্তিগত আইনি পরামর্শের জন্য, অনুগ্রহ করে একজন যোগ্য "
        "পারিবারিক আইন আইনজীবীর সাথে পরামর্শ করুন বা বিনামূল্যে আইনি সহায়তার জন্য আপনার নিকটস্থ "
        f"জেলা আইনি পরিষেবা কর্তৃপক্ষের (DLSA) সাথে যোগাযোগ করুন (হেল্পলাইন: {settings.dlsa_helpline})।"
    ),
    "mr": (
        "⚖️ ही माहिती केवळ शैक्षणिक आणि निर्णय-सहाय्य उद्देशांसाठी आहे. "
        "हा कायदेशीर सल्ला नाही. वैयक्तिक कायदेशीर सल्ल्यासाठी, कृपया योग्य "
        "कौटुंबिक कायदा वकिलाचा सल्ला घ्या किंवा मोफत कायदेशीर मदतीसाठी तुमच्या जवळच्या "
        f"जिल्हा विधी सेवा प्राधिकरणाला (DLSA) भेट द्या (हेल्पलाइन: {settings.dlsa_helpline})।"
    ),
    "gu": (
        "⚖️ આ માહિતી ફક્ત શૈક્ષણિક અને નિર્ણય-સહાય હેતુ માટે છે. "
        "તે કાનૂની સલાહ નથી. વ્યક્તિગત કાનૂની સલાહ માટે, કૃપા કરીને લાયક "
        "કૌટુંબિક કાયદાના વકીલનો સંપર્ક કરો અથવા મફત કાનૂની સહાય માટે તમારી નજીકની "
        f"જિલ્લા કાનૂની સેવા સત્તામંડળ (DLSA) ની મુલાકાત લો (હેલ્પલાઇન: {settings.dlsa_helpline})."
    ),
    "ml": (
        "⚖️ ഈ വിവരങ്ങൾ വിദ്യാഭ്യാസ, തീരുമാന-സഹായ ആവശ്യങ്ങൾക്ക് മാത്രമുള്ളതാണ്. "
        "ഇത് നിയമോപദേശമല്ല. വ്യക്തിഗത നിയമോപദേശത്തിനായി, യോഗ്യതയുള്ള ഒരു "
        "കുടുംബ നിയമ അഭിഭാഷകനെ സമീപിക്കുകയോ സൗജന്യ നിയമ സഹായത്തിനായി നിങ്ങളുടെ അടുത്തുള്ള "
        f"ജില്ലാ ലീഗൽ സർവീസസ് അതോറിറ്റിയെ (DLSA) സന്ദർശിക്കുകയോ ചെയ്യുക (ഹെൽപ്പ്‌ലൈൻ: {settings.dlsa_helpline})."
    ),
    "ur": (
        "⚖️ یہ معلومات صرف تعلیمی اور فیصلہ سازی میں مدد کے مقاصد کے لیے ہے۔ "
        "یہ قانونی مشورہ نہیں ہے۔ ذاتی قانونی مشورے کے لیے، براہ کرم کسی قابل فیملی لا وکیل سے مشورہ کریں "
        f"یا مفت قانونی امداد کے لیے اپنے قریبی ڈسٹرکٹ لیگل سروسز اتھارٹی (DLSA) سے رجوع کریں (ہیلپ لائن: {settings.dlsa_helpline})۔"
    ),
}

# Safe advisory when max retries exhausted
MAX_RETRY_ADVISORY = {
    "en": (
        "Our system could not fully verify all legal provisions for your specific situation. "
        "This may be due to the complexity of your case or the need for more detailed information.\n\n"
        "**We strongly recommend:**\n"
        f"• Visiting your nearest **Family Court** or calling the **DLSA Legal Aid Helpline: {settings.dlsa_helpline}**\n"
        f"• Contacting the **National Commission for Women**: {settings.emergency_helpline_ncw}\n"
        "• Consulting a qualified family law advocate for personalized advice.\n\n"
        "Free legal aid is available to all citizens through the Legal Services Authorities Act, 1987."
    ),
    "hi": (
        "हमारी प्रणाली आपकी विशिष्ट स्थिति के लिए सभी कानूनी प्रावधानों को पूरी तरह सत्यापित नहीं कर सकी। "
        "यह आपके मामले की जटिलता के कारण हो सकता है।\n\n"
        "**हम दृढ़ता से अनुशंसा करते हैं:**\n"
        f"• अपने निकटतम **पारिवारिक न्यायालय** जाएं या **DLSA हेल्पलाइन: {settings.dlsa_helpline}** पर कॉल करें\n"
        f"• **राष्ट्रीय महिला आयोग**: {settings.emergency_helpline_ncw} से संपर्क करें\n"
        "• व्यक्तिगत सलाह के लिए योग्य पारिवारिक कानून वकील से परामर्श करें।"
    ),
    "kn": (
        "ನಮ್ಮ ವ್ಯವಸ್ಥೆಯು ನಿಮ್ಮ ನಿರ್ದಿಷ್ಟ ಪರಿಸ್ಥಿತಿಗೆ ಎಲ್ಲಾ ಕಾನೂನು ನಿಬಂಧನೆಗಳನ್ನು ಸಂಪೂರ್ಣವಾಗಿ ಪರಿಶೀಲಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ।\n\n"
        "**ನಾವು ಬಲವಾಗಿ ಶಿಫಾರಸು ಮಾಡುತ್ತೇವೆ:**\n"
        f"• ನಿಮ್ಮ ಹತ್ತಿರದ **ಕೌಟುಂಬಿಕ ನ್ಯಾಯಾಲಯ**ಕ್ಕೆ ಭೇಟಿ ನೀಡಿ ಅಥವಾ **DLSA ಸಹಾಯವಾಣಿ: {settings.dlsa_helpline}** ಗೆ ಕರೆ ಮಾಡಿ\n"
        f"• **ರಾಷ್ಟ್ರೀಯ ಮಹಿಳಾ ಆಯೋಗ**: {settings.emergency_helpline_ncw} ಸಂಪರ್ಕಿಸಿ"
    ),
}


# ------------------------------------------------------------------ #
# Plain-Language Simplifier
# ------------------------------------------------------------------ #

SIMPLIFIER_SYSTEM_PROMPT = """You are a compassionate Indian Family Law communicator.

Your task: Convert a detailed legal analysis into clear, warm, and accessible language
that a common citizen with no legal background can understand.

Rules:
1. Keep ALL legal information accurate — do not omit important rights or procedures.
2. Replace legal jargon with plain words (e.g., "petition" → "application to the court").
3. Maintain the structure: Rights, Steps to take, Important things to know.
4. Keep citations (Section numbers, Act names) — they are essential for citizen empowerment.
5. Use bullet points and short paragraphs for readability.
6. Write in the specified target language.
7. Be warm and empathetic — the user may be going through a difficult time.
"""


async def _simplify_for_citizen(reasoning_draft: str, lang: str) -> str:
    """Uses Gemini to convert the technical reasoning into plain citizen language."""
    client = genai.Client(api_key=settings.gemini_api_key)

    lang_instruction = {
        "en": "Write in clear, simple English.",
        "hi": "स्पष्ट और सरल हिंदी में लिखें।",
        "kn": "ಸ್ಪಷ್ಟ ಮತ್ತು ಸರಳ ಕನ್ನಡದಲ್ಲಿ ಬರೆಯಿರಿ.",
        "te": "స్పష్టమైన మరియు సరళమైన తెలుగులో వ్రాయండి.",
        "ta": "தெளிவான மற்றும் எளிமையான தமிழில் எழுதவும்.",
        "bn": "স্পষ্ট এবং সহজ বাংলায় লিখুন।",
        "mr": "स्पष्ट आणि सोप्या मराठीत लिहा.",
        "gu": "સ્પષ્ટ અને સરળ ગુજરાતીમાં લખો.",
        "ml": "വ്യക്തവും ലളിതവുമായ മലയാളത്തിൽ എഴുതുക.",
        "ur": "واضح اور آسان اردو میں لکھیں۔",
    }.get(lang, "Write in clear, simple English.")

    prompt = f"""Target Language: {lang}
{lang_instruction}

Convert this legal analysis into plain, accessible citizen-friendly language:

{reasoning_draft}"""

    response = client.models.generate_content(
        model=settings.gemini_llm_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SIMPLIFIER_SYSTEM_PROMPT,
            temperature=0.4,
            max_output_tokens=1500,
        ),
    )
    return response.text


# ------------------------------------------------------------------ #
# Agent Node
# ------------------------------------------------------------------ #

async def response_node(state: LegalAgentState) -> dict:
    """
    LangGraph node: Formats the final two-layer multilingual response.
    Handles emergency fast-path, clarification branch, and normal responses.
    """
    lang_enum = state.get("target_response_language", Language.ENGLISH)
    lang = lang_enum.value if hasattr(lang_enum, "value") else "en"
    disclaimer = DISCLAIMERS.get(lang, DISCLAIMERS["en"])
    reranked = state.get("reranked_passages", [])

    # ── Case 1: Emergency Fast-Path ───────────────────────────────────
    if state.get("is_emergency"):
        emergency_text = state.get("emergency_response", "")
        logger.info("[ResponseAgent] Emergency response path.")
        return {
            "final_response": ResponseLayer(
                plain_language_summary=emergency_text,
                statutory_citations=[],
                disclaimer=disclaimer,
                helplines={
                    "ncw": settings.emergency_helpline_ncw,
                    "emergency": settings.emergency_helpline_general,
                    "dlsa": settings.dlsa_helpline,
                },
            )
        }

    # ── Case 2: Clarification Needed ─────────────────────────────────
    if state.get("needs_clarification"):
        from app.agents.context_agent import _clarification_preamble
        preamble = _clarification_preamble(lang)
        logger.info(f"[ResponseAgent] Clarification branch — asking user for more info in {lang}.")
        return {
            "final_response": ResponseLayer(
                plain_language_summary=preamble,
                statutory_citations=[],
                disclaimer=disclaimer,
            )
        }

    # ── Case 3: Max Retries Exhausted (Verification never passed) ────
    verification_result = state.get("verification_result")
    retry_count = state.get("retry_count", 0)
    if (
        verification_result
        and verification_result.status == VerificationStatus.FAILED
        and retry_count >= settings.verification_max_retries
    ):
        advisory = MAX_RETRY_ADVISORY.get(lang, MAX_RETRY_ADVISORY["en"])
        logger.warning("[ResponseAgent] Max retries exhausted — returning legal aid advisory.")
        return {
            "final_response": ResponseLayer(
                plain_language_summary=advisory,
                statutory_citations=[],
                disclaimer=disclaimer,
                helplines={
                    "ncw": settings.emergency_helpline_ncw,
                    "dlsa": settings.dlsa_helpline,
                },
            )
        }

    # ── Case 4: Normal Verified Response ─────────────────────────────
    reasoning_draft = state.get("reasoning_draft", "")

    if not reasoning_draft:
        plain_summary = MAX_RETRY_ADVISORY.get(lang, MAX_RETRY_ADVISORY["en"])
    else:
        try:
            plain_summary = await _simplify_for_citizen(reasoning_draft, lang)
        except Exception as e:
            logger.error(f"[ResponseAgent] Simplification failed: {e}. Using draft directly.")
            plain_summary = reasoning_draft

    # Build Layer 2: Statutory citations from reranked passages
    citations = [
        {
            "act_name": p.act_name,
            "section_number": p.section_number,
            "section_title": p.section_title,
            "content_excerpt": p.content[:400] + "..." if len(p.content) > 400 else p.content,
            "full_text": p.content,
            "source_url": p.source_url or f"https://indiankanoon.org/search/?formInput={urllib.parse.quote_plus(f'{p.act_name} Section {p.section_number}')}",
            "relevance_score": round(p.relevance_score, 4),
        }
        for p in reranked
    ]

    logger.info(
        f"[ResponseAgent] Final response ready. "
        f"Language: {lang} | Citations: {len(citations)} | "
        f"Summary length: {len(plain_summary)} chars"
    )

    return {
        "final_response": ResponseLayer(
            plain_language_summary=plain_summary,
            statutory_citations=citations,
            disclaimer=disclaimer,
        )
    }
