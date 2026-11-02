"""
Agent Forge - LangGraph Orchestration Graph

This module defines and compiles the full multi-agent LangGraph StateGraph.
It is the central workflow that connects all agent nodes and conditional edges.

Agents wired in this graph:
    1. input_processing_node   → Language detection & ASR transcription
    2. safety_check_node       → Emergency / Domestic Violence fast-path
    3. intent_node             → Legal intent classification
    4. context_node            → Case fact extraction & clarification check
    5. planner_node            → Retrieval strategy formulation
    6. retrieval_node          → Hybrid Qdrant search + Govt API
    7. reasoning_node          → Legal reasoning & synthesis
    8. verification_node       → Grounding check & diagnostic feedback
    9. response_node           → Two-layer multilingual response formatting
"""

import logging
import urllib.parse
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.state import LegalAgentState, VerificationStatus
from app.core.config import get_settings

logger = logging.getLogger("agent_forge.graph")
settings = get_settings()


# ------------------------------------------------------------------ #
# Lazy imports of individual agent nodes
# (imported here to keep graph.py clean and allow independent testing)
# ------------------------------------------------------------------ #

def _get_agents():
    from app.agents.intent_agent import intent_node
    from app.agents.context_agent import context_node
    from app.agents.planner_agent import planner_node
    from app.agents.retrieval_agent import retrieval_node
    from app.agents.reasoning_agent import reasoning_node
    from app.agents.verification_agent import verification_node
    from app.agents.response_agent import response_node
    return (
        intent_node, context_node, planner_node,
        retrieval_node, reasoning_node, verification_node, response_node,
    )


# ------------------------------------------------------------------ #
# Inline Lightweight Nodes (defined here for simplicity)
# ------------------------------------------------------------------ #

async def input_processing_node(state: LegalAgentState) -> dict:
    """
    Node 1: Input Processing
    - Detects language from the user query.
    - If input_mode is 'voice', ASR transcription was already done by the API layer.
    """
    from app.speech.asr_service import detect_language

    query = state["user_query"]
    hint = state.get("target_response_language")
    hint_val = hint.value if hasattr(hint, "value") else str(hint) if hint else None

    detected = await detect_language(query, hint=hint_val)
    logger.info(f"Language detected: {detected.value}")

    return {
        "detected_language": detected,
        "target_response_language": detected,
    }


async def safety_check_node(state: LegalAgentState) -> dict:
    """
    Node 2: Emergency Fast-Path
    - Scans the query for domestic violence / physical danger signals.
    - If detected, sets is_emergency=True and prepares an emergency response.
    """
    import google.genai as genai
    from app.core.state import Language

    query = state["user_query"]
    lang = state.get("detected_language", Language.ENGLISH)
    cfg = get_settings()

    client = genai.Client(api_key=cfg.gemini_api_key)

    prompt = f"""You are a safety classifier for a legal support system.
Analyze the following user query and determine if it describes:
- Immediate physical danger, violence, or threats to life
- Being forcibly evicted or locked out of the home
- Immediate threat to children's safety

Reply with ONLY: YES or NO

Query: "{query}"
"""
    response = client.models.generate_content(
        model=cfg.gemini_llm_model,
        contents=prompt,
    )
    is_emergency = response.text.strip().upper().startswith("YES")

    if is_emergency:
        lang_val = lang.value if hasattr(lang, "value") else str(lang)
        emergency_msg = _build_emergency_response(lang_val, cfg)
        logger.warning(f"🚨 EMERGENCY detected in query: '{query[:60]}...'")
        return {"is_emergency": True, "emergency_response": emergency_msg}

    return {"is_emergency": False}


def _build_emergency_response(language: str, cfg) -> str:
    """Builds an immediate emergency response with helplines."""
    messages = {
        "en": (
            "🚨 **Your safety is the top priority.**\n\n"
            "If you are in immediate danger, please contact:\n"
            f"• **National Emergency**: {cfg.emergency_helpline_general}\n"
            f"• **NCW Women's Helpline**: {cfg.emergency_helpline_ncw}\n"
            f"• **Legal Aid (NALSA)**: {cfg.dlsa_helpline}\n\n"
            "**Your legal rights under the Protection of Women from Domestic Violence Act, 2005:**\n"
            "• Section 12: File an application for a Protection Order at any Magistrate Court.\n"
            "• Section 17: You have the right to reside in the shared household — "
            "you cannot be evicted without a court order.\n"
            "• Section 23: A Magistrate can issue an **ex-parte interim Protection Order** "
            "immediately, even without notifying the respondent.\n\n"
            "Please reach out to a Protection Officer or Shelter Home in your district for immediate help."
        ),
        "hi": (
            "🚨 **आपकी सुरक्षा सर्वोच्च प्राथमिकता है।**\n\n"
            "यदि आप तत्काल खतरे में हैं, कृपया संपर्क करें:\n"
            f"• **राष्ट्रीय आपातकालीन**: {cfg.emergency_helpline_general}\n"
            f"• **महिला हेल्पलाइन (NCW)**: {cfg.emergency_helpline_ncw}\n"
            f"• **कानूनी सहायता (NALSA)**: {cfg.dlsa_helpline}\n\n"
            "**घरेलू हिंसा अधिनियम, 2005 के तहत आपके अधिकार:**\n"
            "• धारा 12: किसी भी मजिस्ट्रेट न्यायालय में संरक्षण आदेश के लिए आवेदन करें।\n"
            "• धारा 17: आपको साझा घर में रहने का अधिकार है — "
            "बिना न्यायालय के आदेश के आपको बेदखल नहीं किया जा सकता।\n"
            "• धारा 23: मजिस्ट्रेट तुरंत **अंतरिम संरक्षण आदेश** जारी कर सकता है।"
        ),
        "kn": (
            "🚨 **ನಿಮ್ಮ ಸುರಕ್ಷತೆ ಅತ್ಯಂತ ಮಹತ್ವದ್ದು.**\n\n"
            "ನೀವು ತಕ್ಷಣದ ಅಪಾಯದಲ್ಲಿದ್ದರೆ, ದಯವಿಟ್ಟು ಸಂಪರ್ಕಿಸಿ:\n"
            f"• **ರಾಷ್ಟ್ರೀಯ ತುರ್ತು ಸೇವೆ**: {cfg.emergency_helpline_general}\n"
            f"• **ಮಹಿಳಾ ಸಹಾಯವಾಣಿ (NCW)**: {cfg.emergency_helpline_ncw}\n"
            f"• **ಕಾನೂನು ನೆರವು (NALSA)**: {cfg.dlsa_helpline}\n\n"
            "**ಘರೇಲು ಹಿಂಸೆ ಕಾಯ್ದೆ, 2005 ರ ಅಡಿಯಲ್ಲಿ ನಿಮ್ಮ ಹಕ್ಕುಗಳು:**\n"
            "• ಕಲಂ 12: ಯಾವುದೇ ನ್ಯಾಯಾಲಯದಲ್ಲಿ ರಕ್ಷಣಾ ಆದೇಶಕ್ಕಾಗಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ।\n"
            "• ಕಲಂ 17: ನೀವು ಸಂಸಾರ ಮನೆಯಲ್ಲಿ ವಾಸಿಸಲು ಹಕ್ಕು ಹೊಂದಿದ್ದೀರಿ।\n"
            "• ಕಲಂ 23: ನ್ಯಾಯಾಧೀಶರು ತಕ್ಷಣ **ಮಧ್ಯಂತರ ರಕ್ಷಣಾ ಆದೇಶ** ನೀಡಬಹುದು।"
        ),
        "te": (
            "🚨 **మీ భద్రత మా మొదటి ప్రాధాన్యత.**\n\n"
            "మీరు తక్షణ ప్రమాదంలో ఉంటే, దయచేసి వెంటనే సంప్రదించండి:\n"
            f"• **జాతీయ అత్యవసర విభాగం**: {cfg.emergency_helpline_general}\n"
            f"• **మహిళా హెల్ప్‌లైన్ (NCW)**: {cfg.emergency_helpline_ncw}\n"
            f"• **ఉచిత న్యాయ సహాయం (NALSA)**: {cfg.dlsa_helpline}\n\n"
            "**గృహహింస రక్షణ చట్టం, 2005 ప్రకారం మీ హక్కులు:**\n"
            "• సెక్షన్ 12: రక్షణ ఉత్తర్వు కోసం మేజిస్ట్రేట్ కోర్టులో దరఖాస్తు చేసుకోండి.\n"
            "• సెక్షన్ 17: నివాస గృహంలో ఉండే హక్కు మీకు ఉంది — కోర్టు ఆదేశం లేకుండా మిమ్మల్ని తొలగించలేరు.\n"
            "• సెక్షన్ 23: మేజిస్ట్రేట్ తక్షణమే **మధ్యంతర రక్షణ ఉత్తర్వు (Ex-parte Order)** జారీ చేయవచ్చు."
        ),
        "ta": (
            "🚨 **உங்கள் பாதுகாப்பே முதன்மையானது.**\n\n"
            "நீங்கள் உடனடி ஆபத்தில் இருந்தால், தயவுசெய்து தொடர்பு கொள்ளவும்:\n"
            f"• **தேசிய அவசர எண்**: {cfg.emergency_helpline_general}\n"
            f"• **மகளிர் உதவி எண் (NCW)**: {cfg.emergency_helpline_ncw}\n"
            f"• **இலவச சட்ட உதவி (NALSA)**: {cfg.dlsa_helpline}\n\n"
            "**குடும்ப வன்முறை தடுப்புச் சட்டம், 2005-ன் கீழ் உங்கள் உரிமைகள்:**\n"
            "• பிரிவு 12: பாதுகாப்பு உத்தரவு கோரி நீதிமன்றத்தில் மனு தாக்கல் செய்யலாம்.\n"
            "• பிரிவு 17: பகிர்வு இல்லத்தில் வசிக்கும் உரிமை உங்களுக்கு உண்டு.\n"
            "• பிரிவு 23: நீதிபதி உடனடியாக **இடைக்கால பாதுகாப்பு உத்தரவை** வழங்க முடியும்."
        ),
        "bn": (
            "🚨 **আপনার সুরক্ষা আমাদের সর্বোচ্চ অগ্রাধিকার।**\n\n"
            "আপনি যদি অবিলম্বে বিপদে পড়েন, অনুগ্রহ করে যোগাযোগ করুন:\n"
            f"• **জাতীয় জরুরি সেবা**: {cfg.emergency_helpline_general}\n"
            f"• **মহিলা হেল্পলাইন (NCW)**: {cfg.emergency_helpline_ncw}\n"
            f"• **বিনামূল্যে আইনি সহায়তা (NALSA)**: {cfg.dlsa_helpline}\n\n"
            "**গার্হস্থ্য হিংসা প্রতিরোধ আইন, ২০০৫ এর অধীনে আপনার অধিকার:**\n"
            "• ধারা ১২: সুরক্ষা আদেশের জন্য ম্যাজিস্ট্রেট আদালতে আবেদন করুন।\n"
            "• ধারা ১৭: ভাগ করা পরিবারে বসবাসের অধিকার আপনার রয়েছে।\n"
            "• ধারা ২৩: ম্যাজিস্ট্রেট অবিলম্বে **অন্তর্বর্তীকালীন সুরক্ষা আদেশ** জারি করতে পারেন।"
        ),
        "mr": (
            "🚨 **तुमची सुरक्षितता ही सर्वोच्च प्राथमिकता आहे.**\n\n"
            "तुम्ही तात्काळ धोक्यात असल्यास, कृपया संपर्क साधा:\n"
            f"• **राष्ट्रीय आणीबाणी**: {cfg.emergency_helpline_general}\n"
            f"• **महिला हेल्पलाइन (NCW)**: {cfg.emergency_helpline_ncw}\n"
            f"• **मोफत कायदेशीर मदत (NALSA)**: {cfg.dlsa_helpline}\n\n"
            "**घरगुती हिंसाचार प्रतिबंधक कायदा, २००५ अंतर्गत तुमचे हक्क:**\n"
            "• कलम १२: संरक्षण आदेशासाठी न्यायदंडाधिकारी न्यायालयात अर्ज करा.\n"
            "• कलम १७: सामायिक घरात राहण्याचा तुम्हाला पूर्ण अधिकार आहे.\n"
            "• कलम २३: दंडाधिकारी तात्काळ **अंतरिम संरक्षण आदेश** जारी करू शकतात."
        ),
        "gu": (
            "🚨 **તમારી સુરક્ષા સર્વોચ્ચ પ્રાથમિકતા છે.**\n\n"
            "જો તમે તાત્કાલિક જોખમમાં હોવ, તો કૃપા કરીને સંપર્ક કરો:\n"
            f"• **રાષ્ટ્રીય ઈમરજન્સી**: {cfg.emergency_helpline_general}\n"
            f"• **મહિલા હેલ્પલાઇન (NCW)**: {cfg.emergency_helpline_ncw}\n"
            f"• **મફત કાનૂની સહાય (NALSA)**: {cfg.dlsa_helpline}\n\n"
            "**ઘરેલુ હિંસા અધિનિયમ, ૨૦૦૫ હેઠળ તમારા અધિકારો:**\n"
            "• કલમ ૧૨: રક્ષણ આદેશ માટે મેજિસ્ટ્રેટ કોર્ટમાં અરજી કરો.\n"
            "• કલમ ૧૭: સહિયારા ઘરમાં રહેવાનો તમને કાનૂની અધિકાર છે.\n"
            "• કલમ ૨૩: મેજિસ્ટ્રેટ તાત્કાલિક **વચગાળાનો રક્ષણ આદેશ** જારી કરી શકે છે."
        ),
        "ml": (
            "🚨 **നിങ്ങളുടെ സുരക്ഷയ്ക്കാണ് പ്രഥമ പരിഗണന.**\n\n"
            "നിങ്ങൾ അടിയന്തിര അപകടത്തിലാണെങ്കിൽ, ദയവായി ബന്ധപ്പെടുക:\n"
            f"• **ദേശീയ അടിയന്തര നമ്പർ**: {cfg.emergency_helpline_general}\n"
            f"• **വനിതാ ഹെൽപ്പ്‌ലൈൻ (NCW)**: {cfg.emergency_helpline_ncw}\n"
            f"• **സൗജന്യ നിയമ സഹായം (NALSA)**: {cfg.dlsa_helpline}\n\n"
            "**ഗാർഹിക പീഡന നിരോധന നിയമം, 2005 പ്രകാരമുള്ള നിങ്ങളുടെ അവകാശങ്ങൾ:**\n"
            "• വകുപ്പ് 12: പ്രൊട്ടക്ഷൻ ഓർഡറിനായി മജിസ്‌ട്രേറ്റ് കോടതിയിൽ അപേക്ഷ നൽകുക.\n"
            "• വകുപ്പ് 17: പങ്കിട്ട വീട്ടിൽ താമസിക്കാനുള്ള അവകാശം നിങ്ങൾക്കുണ്ട്.\n"
            "• വകുപ്പ് 23: മജിസ്‌ട്രേറ്റിന് ഉടനടി **ഇടക്കാല സംരക്ഷണ ഉത്തരവ്** പുറപ്പെടുവിക്കാം."
        ),
        "ur": (
            "🚨 **آپ کی حفاظت اولین ترجیح ہے۔**\n\n"
            "اگر آپ فوری خطرے میں ہیں، تو براہ کرم رابطہ کریں:\n"
            f"• **قومی ایمرجنسی**: {cfg.emergency_helpline_general}\n"
            f"• **خواتین کی ہیلپ لائن (NCW)**: {cfg.emergency_helpline_ncw}\n"
            f"• **مفت قانونی امداد (NALSA)**: {cfg.dlsa_helpline}\n\n"
            "**گھریلو تشدد ایکٹ، 2005 کے تحت آپ کے حقوق:**\n"
            "• دفعہ 12: تحفظ کے حکم کے لیے مجسٹریٹ کی عدالت میں درخواست دیں۔\n"
            "• دفعہ 17: آپ کو مشترکہ رہائش گاہ میں رہنے کا پورا حق ہے۔\n"
            "• دفعہ 23: مجسٹریٹ فوری طور پر **عبوری تحفظ کا حکم** جاری کر سکتا ہے۔"
        ),
    }
    return messages.get(language, messages["en"])


# ------------------------------------------------------------------ #
# Conditional Edge Functions
# ------------------------------------------------------------------ #

def route_after_safety(state: LegalAgentState) -> str:
    """If emergency → go to response. Otherwise → intent agent."""
    if state.get("is_emergency"):
        return "response_node"
    return "intent_node"


def route_after_context(state: LegalAgentState) -> str:
    """If critical facts are missing → stop for clarification. Otherwise → planner."""
    if state.get("needs_clarification"):
        return "response_node"  # Response agent formats the clarification questions
    return "planner_node"


def route_after_verification(state: LegalAgentState) -> str:
    """Core verification loop: FAIL → retrieval retry (if under limit) | PASS → response."""
    result = state.get("verification_result")
    retry_count = state.get("retry_count", 0)

    if result and result.status == VerificationStatus.FAILED:
        if retry_count < settings.verification_max_retries:
            logger.info(f"Verification FAILED (attempt {retry_count + 1}). Retrying retrieval...")
            return "retrieval_node"
        else:
            logger.warning("Verification FAILED after max retries. Proceeding with advisory response.")
            return "response_node"

    return "response_node"


# ------------------------------------------------------------------ #
# Graph Builder
# ------------------------------------------------------------------ #

def build_graph() -> StateGraph:
    """
    Constructs and compiles the LangGraph multi-agent StateGraph.

    Returns a compiled graph ready for async invocation.
    """
    (
        intent_node, context_node, planner_node,
        retrieval_node, reasoning_node, verification_node, response_node,
    ) = _get_agents()

    graph = StateGraph(LegalAgentState)

    # Add all nodes
    graph.add_node("input_processing_node", input_processing_node)
    graph.add_node("safety_check_node",     safety_check_node)
    graph.add_node("intent_node",           intent_node)
    graph.add_node("context_node",          context_node)
    graph.add_node("planner_node",          planner_node)
    graph.add_node("retrieval_node",        retrieval_node)
    graph.add_node("reasoning_node",        reasoning_node)
    graph.add_node("verification_node",     verification_node)
    graph.add_node("response_node",         response_node)

    # Entry point
    graph.set_entry_point("input_processing_node")

    # Linear edges
    graph.add_edge("input_processing_node", "safety_check_node")
    graph.add_edge("intent_node",           "context_node")
    graph.add_edge("planner_node",          "retrieval_node")
    graph.add_edge("retrieval_node",        "reasoning_node")
    graph.add_edge("reasoning_node",        "verification_node")
    graph.add_edge("response_node",         END)

    # Conditional edges
    graph.add_conditional_edges(
        "safety_check_node",
        route_after_safety,
        {"intent_node": "intent_node", "response_node": "response_node"},
    )
    graph.add_conditional_edges(
        "context_node",
        route_after_context,
        {"planner_node": "planner_node", "response_node": "response_node"},
    )
    graph.add_conditional_edges(
        "verification_node",
        route_after_verification,
        {"retrieval_node": "retrieval_node", "response_node": "response_node"},
    )

    # Compile with in-memory checkpointing for multi-turn conversation memory
    memory = MemorySaver()
    compiled = graph.compile(checkpointer=memory)

    logger.info("✅ LangGraph multi-agent workflow compiled successfully.")
    return compiled


# Singleton compiled graph
_compiled_graph = None


def get_compiled_graph():
    """Returns the singleton compiled LangGraph workflow."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


# ------------------------------------------------------------------ #
# Public Invocation Function
# ------------------------------------------------------------------ #

async def run_legal_agent(
    user_query: str,
    session_id: str,
    language_hint: str | None = None,
    input_mode: str = "text",
) -> dict:
    """
    Primary entry point for running the complete multi-agent legal workflow.
    Called by the /chat API route.
    """
    from app.core.state import Language, InputMode, FamilyLawDomain

    graph = get_compiled_graph()

    # Build initial state — safely handle input_mode as string or enum
    try:
        mode = InputMode(input_mode) if isinstance(input_mode, str) else input_mode
    except ValueError:
        mode = InputMode.TEXT

    valid_lang_values = {l.value for l in Language}
    resolved_hint = Language(language_hint) if language_hint in valid_lang_values else Language.ENGLISH

    initial_state: LegalAgentState = {
        "user_query": user_query,
        "input_mode": mode,
        "audio_file_path": None,
        "detected_language": resolved_hint,
        "target_response_language": resolved_hint,
        "is_emergency": False,
        "emergency_response": None,
        "law_domain": FamilyLawDomain.UNKNOWN,
        "user_intent_summary": "",
        "case_context": None,
        "missing_context_questions": [],
        "needs_clarification": False,
        "retrieval_plan": "",
        "search_query_en": "",
        "search_queries_multilingual": [],
        "retrieved_passages": [],
        "reranked_passages": [],
        "reasoning_draft": "",
        "verification_result": None,
        "retry_count": 0,
        "final_response": None,
        "audio_output_path": None,
        "conversation_history": [],
    }

    config = {"configurable": {"thread_id": session_id}}

    final_state = await graph.ainvoke(initial_state, config=config)

    # Format the API response
    resp = final_state.get("final_response")
    if resp:
        citations = [
            {
                "act_name": p.act_name,
                "section_number": p.section_number,
                "section_title": p.section_title,
                "content_excerpt": p.content[:400] + "..." if len(p.content) > 400 else p.content,
                "full_text": p.content,
                "source_url": p.source_url or f"https://indiankanoon.org/search/?formInput={urllib.parse.quote_plus(f'{p.act_name} Section {p.section_number}')}",
                "relevance_score": p.relevance_score,
            }
            for p in final_state.get("reranked_passages", [])
        ]

        det_lang = final_state.get("detected_language", Language.ENGLISH)
        det_lang_val = det_lang.value if hasattr(det_lang, "value") else str(det_lang)

        law_dom = final_state.get("law_domain", FamilyLawDomain.UNKNOWN)
        law_dom_val = law_dom.value if hasattr(law_dom, "value") else str(law_dom)

        return {
            "session_id": session_id,
            "plain_language_summary": resp.plain_language_summary,
            "statutory_citations": citations,
            "disclaimer": resp.disclaimer,
            "detected_language": det_lang_val,
            "law_domain": law_dom_val,
            "is_emergency": final_state.get("is_emergency", False),
            "emergency_contacts": resp.helplines,
            "needs_clarification": final_state.get("needs_clarification", False),
            "clarification_questions": final_state.get("missing_context_questions", []),
            "audio_available": False,
            "audio_url": None,
        }

    return {
        "session_id": session_id,
        "plain_language_summary": "I was unable to process your query. Please try again.",
        "statutory_citations": [],
        "disclaimer": "This system provides educational information only, not legal advice.",
        "detected_language": "en",
        "law_domain": "unknown",
        "is_emergency": False,
        "emergency_contacts": None,
        "needs_clarification": False,
        "clarification_questions": [],
        "audio_available": False,
        "audio_url": None,
    }
