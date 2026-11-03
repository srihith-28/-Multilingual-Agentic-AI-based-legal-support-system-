"""
Document Drafter Service
========================
Generates bilingual (English + Indian language) legal PDF documents
using ReportLab's Platypus layout engine.

Supported templates:
  - mutual_divorce_petition       (Section 13B HMA / Section 28 SMA)
  - protection_order_application  (Section 12 PWDVA 2005)
  - maintenance_application       (Section 125 CrPC / Section 144 BNSS)
  - rcr_notice                    (Section 9 HMA / Section 22 SMA)
"""

import io
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

logger = logging.getLogger("agent_forge.document_drafter")

# ── Font paths ─────────────────────────────────────────────────────────────────
_FONTS_DIR = Path(__file__).resolve().parent.parent / "static" / "fonts"

# Language → (font name, font file) mapping
# We use reportlab's built-in Helvetica as fallback for English.
# For Indic scripts, we register Noto fonts if present; if not, fallback gracefully.
_LANG_FONT_MAP = {
    "hi": ("NotoSansDevanagari", "NotoSansDevanagari-Regular.ttf"),
    "mr": ("NotoSansDevanagari", "NotoSansDevanagari-Regular.ttf"),
    "kn": ("NotoSansKannada",    "NotoSansKannada-Regular.ttf"),
    "te": ("NotoSansTelugu",     "NotoSansTelugu-Regular.ttf"),
    "ta": ("NotoSansTamil",      "NotoSansTamil-Regular.ttf"),
    "bn": ("NotoSansBengali",    "NotoSansBengali-Regular.ttf"),
    "gu": ("NotoSansGujarati",   "NotoSansGujarati-Regular.ttf"),
    "ml": ("NotoSansMalayalam",  "NotoSansMalayalam-Regular.ttf"),
    "ur": ("NotoNastaliqUrdu",   "NotoNastaliqUrdu-Regular.ttf"),
    "en": ("Helvetica",          None),
}

_registered_fonts: set[str] = set()


def _ensure_font(lang: str) -> str:
    """Register the Noto font for *lang* and return the font name to use."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_name, font_file = _LANG_FONT_MAP.get(lang, ("Helvetica", None))
    if font_file and font_name not in _registered_fonts:
        font_path = _FONTS_DIR / font_file
        if font_path.exists():
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
            _registered_fonts.add(font_name)
            logger.info(f"Registered font: {font_name} from {font_path}")
        else:
            logger.warning(f"Font file not found: {font_path}; falling back to Helvetica")
            font_name = "Helvetica"
    return font_name


# ── Translation strings for document boilerplate ─────────────────────────────
_I18N = {
    "en": {
        "in_the_court": "IN THE COURT OF THE PRINCIPAL FAMILY JUDGE",
        "at": "AT",
        "vs": "VERSUS",
        "date": "Date:",
        "prayer": "PRAYER",
        "verification": "VERIFICATION",
        "petitioner": "PETITIONER",
        "respondent": "RESPONDENT",
        "applicant": "APPLICANT",
        "address": "Address",
        "age": "Age",
        "draft_notice": "[DRAFT - For educational purposes only. Have a qualified advocate review before filing.]",
    },
    "hi": {
        "in_the_court": "मुख्य पारिवारिक न्यायाधीश के न्यायालय में",
        "at": "में",
        "vs": "बनाम",
        "date": "दिनांक:",
        "prayer": "प्रार्थना",
        "verification": "सत्यापन",
        "petitioner": "याचिकाकर्ता",
        "respondent": "प्रतिवादी",
        "applicant": "आवेदक",
        "address": "पता",
        "age": "आयु",
        "draft_notice": "[मसौदा - केवल शैक्षणिक उद्देश्यों के लिए। दाखिल करने से पहले एक योग्य अधिवक्ता से समीक्षा करवाएं।]",
    },
    "kn": {
        "in_the_court": "ಮುಖ್ಯ ಕುಟುಂಬ ನ್ಯಾಯಾಧೀಶರ ನ್ಯಾಯಾಲಯದಲ್ಲಿ",
        "at": "ನಲ್ಲಿ",
        "vs": "ವಿರುದ್ಧ",
        "date": "ದಿನಾಂಕ:",
        "prayer": "ಪ್ರಾರ್ಥನೆ",
        "verification": "ಪರಿಶೀಲನೆ",
        "petitioner": "ಅರ್ಜಿದಾರ",
        "respondent": "ಪ್ರತಿವಾದಿ",
        "applicant": "ಅರ್ಜಿದಾರ",
        "address": "ವಿಳಾಸ",
        "age": "ವಯಸ್ಸು",
        "draft_notice": "[ಕರಡು - ಶೈಕ್ಷಣಿಕ ಉದ್ದೇಶಗಳಿಗಾಗಿ ಮಾತ್ರ]",
    },
    "te": {
        "in_the_court": "ప్రధాన కుటుంబ న్యాయమూర్తి న్యాయస్థానంలో",
        "at": "వద్ద",
        "vs": "వర్సస్",
        "date": "తేదీ:",
        "prayer": "ప్రార్థన",
        "verification": "ధృవీకరణ",
        "petitioner": "పిటిషనర్",
        "respondent": "రెస్పాండెంట్",
        "applicant": "దరఖాస్తుదారు",
        "address": "చిరునామా",
        "age": "వయసు",
        "draft_notice": "[ముసాయిదా - విద్యా ప్రయోజనాల కోసం మాత్రమే]",
    },
    "ta": {
        "in_the_court": "தலைமை குடும்ப நீதிபதி நீதிமன்றத்தில்",
        "at": "இல்",
        "vs": "எதிர்",
        "date": "தேதி:",
        "prayer": "வேண்டுகோள்",
        "verification": "சரிபார்ப்பு",
        "petitioner": "மனுதாரர்",
        "respondent": "பிரதிவாதி",
        "applicant": "விண்ணப்பதாரர்",
        "address": "முகவரி",
        "age": "வயது",
        "draft_notice": "[வரைவு - கல்வி நோக்கங்களுக்காக மட்டுமே]",
    },
    "bn": {
        "in_the_court": "প্রধান পারিবারিক বিচারকের আদালতে",
        "at": "এ",
        "vs": "বনাম",
        "date": "তারিখ:",
        "prayer": "প্রার্থনা",
        "verification": "যাচাইকরণ",
        "petitioner": "আবেদনকারী",
        "respondent": "বিবাদী",
        "applicant": "আবেদনকারী",
        "address": "ঠিকানা",
        "age": "বয়স",
        "draft_notice": "[খসড়া - শুধুমাত্র শিক্ষামূলক উদ্দেশ্যে]",
    },
    "mr": {
        "in_the_court": "मुख्य कौटुंबिक न्यायाधीशांच्या न्यायालयात",
        "at": "येथे",
        "vs": "विरुद्ध",
        "date": "दिनांक:",
        "prayer": "विनंती",
        "verification": "सत्यापन",
        "petitioner": "याचिकाकर्ता",
        "respondent": "प्रतिवादी",
        "applicant": "अर्जदार",
        "address": "पत्ता",
        "age": "वय",
        "draft_notice": "[मसुदा - केवळ शैक्षणिक हेतूंसाठी]",
    },
    "gu": {
        "in_the_court": "મુખ્ય કૌટુંબિક ન્યાયાધીશની અદાલતમાં",
        "at": "ખાતે",
        "vs": "વિરુદ્ધ",
        "date": "તારીખ:",
        "prayer": "પ્રાર્થના",
        "verification": "ચકાસણી",
        "petitioner": "અરજદાર",
        "respondent": "પ્રતિવાદી",
        "applicant": "અરજદાર",
        "address": "સરનામું",
        "age": "ઉંમર",
        "draft_notice": "[મસૌદો - માત્ર શૈક્ષણિક હેતુ માટે]",
    },
    "ml": {
        "in_the_court": "ഹൗസ് ഫാമിലി കോർട്ടിൽ",
        "at": "ൽ",
        "vs": "vs",
        "date": "തീയതി:",
        "prayer": "പ്രാർത്ഥന",
        "verification": "സ്ഥിരീകരണം",
        "petitioner": "ഹർജിക്കാരൻ",
        "respondent": "പ്രതിവാദി",
        "applicant": "അപേക്ഷകൻ",
        "address": "വിലാസം",
        "age": "പ്രായം",
        "draft_notice": "[ഡ്രാഫ്റ്റ് - വിദ്യാഭ്യാസ ആവശ്യങ്ങൾക്ക് മാത്രം]",
    },
}


def _t(key: str, lang: str) -> str:
    """Get translated string, fallback to English."""
    return _I18N.get(lang, _I18N["en"]).get(key, _I18N["en"].get(key, key))


# ── PDF builder helpers ────────────────────────────────────────────────────────
def _build_styles(en_font: str, lang_font: str):
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.lib import colors

    styles = getSampleStyleSheet()
    base = dict(fontName=en_font, fontSize=10, leading=14, textColor=colors.black)

    return {
        "title": ParagraphStyle("title", fontName=en_font, fontSize=14, leading=18,
                                 alignment=TA_CENTER, spaceAfter=6, textColor=colors.HexColor("#1a1a4e"), bold=True),
        "subtitle": ParagraphStyle("subtitle", fontName=en_font, fontSize=10, leading=14,
                                    alignment=TA_CENTER, spaceAfter=3, textColor=colors.HexColor("#333366")),
        "section": ParagraphStyle("section", fontName=en_font, fontSize=11, leading=16,
                                   spaceAfter=4, spaceBefore=8, textColor=colors.HexColor("#1a1a4e"),
                                   bold=True, underline=True),
        "body_en": ParagraphStyle("body_en", fontName=en_font, fontSize=9, leading=13,
                                   textColor=colors.HexColor("#111111"), alignment=TA_JUSTIFY),
        "body_lang": ParagraphStyle("body_lang", fontName=lang_font, fontSize=9, leading=14,
                                     textColor=colors.HexColor("#222244"), alignment=TA_JUSTIFY),
        "disclaimer": ParagraphStyle("disclaimer", fontName=en_font, fontSize=7.5, leading=11,
                                      textColor=colors.HexColor("#884400"), alignment=TA_CENTER,
                                      spaceBefore=12),
    }


def _header_block(court_district: str, lang: str, styles: dict):
    """Return top-of-document Paragraph elements."""
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.units import mm

    elems = []
    elems.append(Paragraph("🏛 AGENT FORGE LEGAL DOCUMENT SYSTEM", styles["subtitle"]))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(f"{_t('in_the_court', 'en')} {_t('at', 'en')} {court_district.upper()}", styles["title"]))
    if lang != "en":
        elems.append(Paragraph(f"{_t('in_the_court', lang)} {_t('at', lang)} {court_district}", styles["subtitle"]))
    elems.append(Spacer(1, 4 * mm))
    return elems


def _bilingual_row(en_text: str, lang_text: str, styles: dict, lang: str):
    """Return a two-column table row with English left and vernacular right."""
    from reportlab.platypus import Table, TableStyle, Paragraph
    from reportlab.lib import colors

    if lang == "en":
        return [Paragraph(en_text, styles["body_en"])]

    table = Table(
        [[Paragraph(en_text, styles["body_en"]), Paragraph(lang_text, styles["body_lang"])]],
        colWidths=["50%", "50%"],
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, colors.HexColor("#ccccdd")),
    ]))
    return [table]


def _disclaimer(lang: str, styles: dict):
    from reportlab.platypus import Paragraph, HRFlowable
    from reportlab.lib import colors
    return [
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#884400")),
        Paragraph(f"⚠ {_t('draft_notice', lang)}", styles["disclaimer"]),
        Paragraph(f"⚠ {_t('draft_notice', 'en')}", styles["disclaimer"]),
        Paragraph(f"Generated on {datetime.now().strftime('%d %B %Y')} | Agent Forge Legal AI System", styles["disclaimer"]),
    ]


# ── Individual template generators ────────────────────────────────────────────

def _divorce_petition(d: dict, lang: str, styles: dict) -> list:
    from reportlab.platypus import Paragraph, Spacer, HRFlowable
    from reportlab.lib.units import mm
    from reportlab.lib import colors

    court = d.get("court_district", "________")
    p1_name = d.get("petitioner1_name", "________")
    p1_age  = d.get("petitioner1_age",  "___")
    p1_addr = d.get("petitioner1_address", "________")
    p2_name = d.get("petitioner2_name", "________")
    p2_age  = d.get("petitioner2_age",  "___")
    p2_addr = d.get("petitioner2_address", "________")
    m_date  = d.get("marriage_date",     "________")
    m_place = d.get("marriage_place",    "________")
    sep_date = d.get("separation_date",  "________")

    elems = _header_block(court, lang, styles)

    elems.append(Paragraph("PETITION FOR MUTUAL CONSENT DIVORCE<br/>Under Section 13B of the Hindu Marriage Act, 1955", styles["title"]))
    if lang != "en":
        elems.append(Paragraph(f"आपसी सहमति से तलाक की याचिका | ಪರಸ್ಪರ ಒಪ್ಪಿಗೆ ವಿಚ್ಛೇದನ ಅರ್ಜಿ", styles["subtitle"]))
    elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a1a4e")))
    elems.append(Spacer(1, 3 * mm))

    # Parties
    elems.append(Paragraph(f"<b>{p1_name}</b>, Age: {p1_age}  — Petitioner No. 1 (Husband)", styles["body_en"]))
    elems.append(Paragraph(f"<b>{p2_name}</b>, Age: {p2_age}  — Petitioner No. 2 (Wife)", styles["body_en"]))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph("PETITION", styles["section"]))

    paras_en = [
        f"That the Petitioners were married according to Hindu rites and ceremonies on <b>{m_date}</b> at <b>{m_place}</b>.",
        f"That the Petitioners have been living separately since <b>{sep_date}</b> and have not cohabited as husband and wife thereafter.",
        "That there is no possibility of reconciliation between the Petitioners.",
        "That the Petitioners have mutually agreed to dissolve the marriage.",
        f"Address of Petitioner 1: {p1_addr}",
        f"Address of Petitioner 2: {p2_addr}",
    ]
    paras_hi = [
        f"कि याचिकाकर्ताओं की शादी हिंदू रीति-रिवाजों के अनुसार <b>{m_date}</b> को <b>{m_place}</b> में हुई थी।",
        f"कि याचिकाकर्ता <b>{sep_date}</b> से अलग रह रहे हैं और उसके बाद पति-पत्नी के रूप में साथ नहीं रहे हैं।",
        "कि याचिकाकर्ताओं के बीच सुलह की कोई संभावना नहीं है।",
        "कि याचिकाकर्ताओं ने आपसी सहमति से विवाह विच्छेद के लिए सहमति दी है।",
        f"याचिकाकर्ता 1 का पता: {p1_addr}",
        f"याचिकाकर्ता 2 का पता: {p2_addr}",
    ]
    _lang_paras = paras_hi  # default for non-mapped lang

    for i, en_p in enumerate(paras_en):
        lang_p = (paras_hi[i] if lang == "hi" else en_p)
        elems.extend(_bilingual_row(en_p, lang_p, styles, lang))
        elems.append(Spacer(1, 2 * mm))

    elems.append(Paragraph("PRAYER", styles["section"]))
    elems.extend(_bilingual_row(
        "Wherefore, the Petitioners most respectfully pray that this Hon'ble Court may be pleased to pass a decree of divorce by mutual consent dissolving the marriage between the Petitioners.",
        "अतः याचिकाकर्ता इस माननीय न्यायालय से विनम्रतापूर्वक प्रार्थना करते हैं कि याचिकाकर्ताओं के बीच विवाह को आपसी सहमति से विघटित करने का डिक्री पारित करने की कृपा करें।",
        styles, lang
    ))

    elems.append(Spacer(1, 4 * mm))
    elems.append(Paragraph("VERIFICATION", styles["section"]))
    elems.extend(_bilingual_row(
        f"We, {p1_name} and {p2_name}, do hereby verify that the contents of this petition are true and correct to the best of our knowledge.",
        f"हम, {p1_name} और {p2_name}, एतद्द्वारा सत्यापित करते हैं कि इस याचिका की सामग्री हमारी सर्वोत्तम जानकारी के अनुसार सत्य और सही है।",
        styles, lang
    ))
    elems.append(Spacer(1, 8 * mm))
    elems.append(Paragraph("Signature of Petitioner 1: _____________________ &nbsp;&nbsp;&nbsp; Signature of Petitioner 2: _____________________", styles["body_en"]))
    elems.append(Spacer(1, 4 * mm))
    elems.extend(_disclaimer(lang, styles))
    return elems


def _protection_order(d: dict, lang: str, styles: dict) -> list:
    from reportlab.platypus import Paragraph, Spacer, HRFlowable
    from reportlab.lib.units import mm
    from reportlab.lib import colors

    court = d.get("court_district", "________")
    app_name = d.get("applicant_name", "________")
    app_age  = d.get("applicant_age", "___")
    app_addr = d.get("applicant_address", "________")
    res_name = d.get("respondent_name", "________")
    res_rel  = d.get("respondent_relation", "________")
    res_addr = d.get("respondent_address", "________")
    inc_date = d.get("incident_date", "________")
    inc_desc = d.get("incident_description", "________")

    elems = _header_block(court, lang, styles)
    elems.append(Paragraph("APPLICATION FOR PROTECTION ORDER<br/>Under Section 12 of the Protection of Women from Domestic Violence Act, 2005", styles["title"]))
    elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a1a4e")))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(f"<b>Applicant:</b> {app_name}, Age: {app_age}<br/><b>Address:</b> {app_addr}", styles["body_en"]))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(f"<b>Respondent:</b> {res_name} ({res_rel})<br/><b>Address:</b> {res_addr}", styles["body_en"]))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph("FACTS OF THE CASE", styles["section"]))
    elems.extend(_bilingual_row(
        f"On or about {inc_date}, the Respondent committed acts of domestic violence against the Applicant as described below: {inc_desc}",
        f"{inc_date} को या उसके आसपास, प्रतिवादी ने आवेदक के खिलाफ घरेलू हिंसा के कार्य किए: {inc_desc}",
        styles, lang
    ))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph("PRAYER", styles["section"]))
    elems.extend(_bilingual_row(
        "The Applicant most respectfully prays for: (a) Protection Order under Section 18 PWDVA, (b) Residence Order under Section 19 PWDVA, (c) Monetary Relief under Section 20 PWDVA.",
        "आवेदक निम्नलिखित के लिए प्रार्थना करती/करता है: (a) धारा 18 PWDVA के तहत संरक्षण आदेश, (b) धारा 19 PWDVA के तहत निवास आदेश, (c) धारा 20 PWDVA के तहत मौद्रिक राहत।",
        styles, lang
    ))
    elems.append(Spacer(1, 6 * mm))
    elems.append(Paragraph("Signature of Applicant: _____________________", styles["body_en"]))
    elems.append(Spacer(1, 2 * mm))
    elems.extend(_disclaimer(lang, styles))
    return elems


def _maintenance_application(d: dict, lang: str, styles: dict) -> list:
    from reportlab.platypus import Paragraph, Spacer, HRFlowable
    from reportlab.lib.units import mm
    from reportlab.lib import colors

    court    = d.get("court_district", "________")
    app_name = d.get("applicant_name", "________")
    app_age  = d.get("applicant_age", "___")
    app_addr = d.get("applicant_address", "________")
    res_name = d.get("respondent_name", "________")
    res_addr = d.get("respondent_address", "________")
    m_date   = d.get("marriage_date", "________")
    res_inc  = d.get("respondent_income", "________")
    app_inc  = d.get("applicant_income", "0")
    n_child  = d.get("num_children", "0")
    expenses = d.get("monthly_expenses", "________")

    elems = _header_block(court, lang, styles)
    elems.append(Paragraph("APPLICATION FOR MAINTENANCE<br/>Under Section 125 CrPC / Section 144 BNSS", styles["title"]))
    elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a1a4e")))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(f"<b>Applicant:</b> {app_name}, Age: {app_age}, Address: {app_addr}", styles["body_en"]))
    elems.append(Paragraph(f"<b>Respondent:</b> {res_name}, Address: {res_addr}", styles["body_en"]))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph("GROUNDS", styles["section"]))
    paras = [
        (f"That the Applicant and Respondent were married on {m_date}.",
         f"कि आवेदक और प्रतिवादी का विवाह {m_date} को हुआ था।"),
        (f"That the Respondent has a monthly income of approximately ₹{res_inc} and the Applicant earns ₹{app_inc} per month.",
         f"कि प्रतिवादी की मासिक आय लगभग ₹{res_inc} है और आवेदक की आय ₹{app_inc} प्रति माह है।"),
        (f"That the Applicant's monthly expenses are approximately ₹{expenses} inclusive of {n_child} minor children.",
         f"कि आवेदक का मासिक खर्च {n_child} अवयस्क बच्चों सहित लगभग ₹{expenses} है।"),
        ("That the Respondent has neglected or refused to maintain the Applicant despite having sufficient means.",
         "कि प्रतिवादी ने पर्याप्त साधन होने के बावजूद आवेदक का भरण-पोषण करने से इनकार कर दिया है।"),
    ]
    for en_p, hi_p in paras:
        lang_p = hi_p if lang == "hi" else en_p
        elems.extend(_bilingual_row(en_p, lang_p, styles, lang))
        elems.append(Spacer(1, 2 * mm))

    elems.append(Paragraph("PRAYER", styles["section"]))
    elems.extend(_bilingual_row(
        "The Applicant prays that the Respondent be directed to pay reasonable monthly maintenance as per the guidelines in Rajnesh v. Neha (2020) 14 SCC 1.",
        "आवेदक प्रार्थना करता/करती है कि प्रतिवादी को राजनेश बनाम नेहा (2020) 14 SCC 1 के दिशानिर्देशों के अनुसार उचित मासिक भरण-पोषण का भुगतान करने का निर्देश दिया जाए।",
        styles, lang
    ))
    elems.append(Spacer(1, 6 * mm))
    elems.append(Paragraph("Signature: _____________________", styles["body_en"]))
    elems.append(Spacer(1, 2 * mm))
    elems.extend(_disclaimer(lang, styles))
    return elems


def _rcr_notice(d: dict, lang: str, styles: dict) -> list:
    from reportlab.platypus import Paragraph, Spacer, HRFlowable
    from reportlab.lib.units import mm
    from reportlab.lib import colors

    court    = d.get("court_district", "________")
    s_name   = d.get("sender_name", "________")
    s_addr   = d.get("sender_address", "________")
    r_name   = d.get("recipient_name", "________")
    r_addr   = d.get("recipient_address", "________")
    m_date   = d.get("marriage_date", "________")
    sep_date = d.get("separation_date", "________")
    reason   = d.get("reason_given", "No reason given.")

    elems = _header_block(court, lang, styles)
    elems.append(Paragraph("LEGAL NOTICE<br/>FOR RESTITUTION OF CONJUGAL RIGHTS<br/>Under Section 9 of the Hindu Marriage Act, 1955", styles["title"]))
    elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a1a4e")))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(f"<b>From:</b> {s_name}<br/>{s_addr}", styles["body_en"]))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(f"<b>To:</b> {r_name}<br/>{r_addr}", styles["body_en"]))
    elems.append(Spacer(1, 3 * mm))

    paras = [
        (f"TAKE NOTICE that you and the undersigned {s_name} were married on {m_date} as per Hindu rites.",
         f"नोटिस लें कि आप और अधोहस्ताक्षरी {s_name} का विवाह हिंदू रीति के अनुसार {m_date} को हुआ था।"),
        (f"That on or about {sep_date}, you withdrew from the company and society of the undersigned without reasonable cause.",
         f"कि {sep_date} को या उसके आसपास, आपने बिना उचित कारण के अधोहस्ताक्षरी की संगति और समाज से हट गए।"),
        (f"Reason you stated (if any): {reason}",
         f"आपका कारण (यदि कोई): {reason}"),
        ("You are hereby called upon to return to the matrimonial home and resume cohabitation within 30 days of receipt of this notice, failing which my client will be constrained to file a petition for Restitution of Conjugal Rights before the competent Family Court.",
         "आपसे अनुरोध है कि इस नोटिस की प्राप्ति के 30 दिनों के भीतर वैवाहिक घर वापस आएं, अन्यथा सक्षम न्यायालय में वैवाहिक अधिकारों की बहाली के लिए याचिका दायर की जाएगी।"),
    ]
    for en_p, hi_p in paras:
        lang_p = hi_p if lang == "hi" else en_p
        elems.extend(_bilingual_row(en_p, lang_p, styles, lang))
        elems.append(Spacer(1, 2 * mm))

    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph(f"Yours sincerely,<br/>{s_name}", styles["body_en"]))
    elems.append(Spacer(1, 2 * mm))
    elems.extend(_disclaimer(lang, styles))
    return elems


# ── Public API ─────────────────────────────────────────────────────────────────
TEMPLATE_MAP = {
    "mutual_divorce_petition": _divorce_petition,
    "protection_order_application": _protection_order,
    "maintenance_application": _maintenance_application,
    "rcr_notice": _rcr_notice,
}


def generate_legal_document_pdf(
    template_type: str,
    party_details: dict[str, Any],
    language: str = "en",
) -> bytes:
    """
    Generate a bilingual legal PDF and return the raw bytes.

    :param template_type: One of TEMPLATE_MAP keys
    :param party_details: Dict of form field values
    :param language: Target vernacular language code (en = English only)
    :returns: PDF bytes
    :raises ValueError: if template_type unknown
    :raises ImportError: if reportlab not installed
    """
    try:
        from reportlab.platypus import SimpleDocTemplate, Spacer
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
    except ImportError as e:
        raise ImportError("reportlab is required for PDF generation. Run: pip install reportlab") from e

    if template_type not in TEMPLATE_MAP:
        raise ValueError(f"Unknown template_type: {template_type!r}. Choose from: {list(TEMPLATE_MAP.keys())}")

    # Normalise language
    lang = language.lower() if language else "en"
    if lang not in _I18N:
        lang = "en"

    # Ensure fonts
    en_font   = "Helvetica"
    lang_font = _ensure_font(lang) if lang != "en" else "Helvetica"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Agent Forge Legal Document",
        author="Agent Forge Legal AI",
    )

    styles = _build_styles(en_font, lang_font)
    template_fn = TEMPLATE_MAP[template_type]
    story = template_fn(party_details, lang, styles)

    doc.build(story)
    pdf_bytes = buf.getvalue()
    logger.info(f"Generated PDF: template={template_type}, lang={lang}, size={len(pdf_bytes)} bytes")
    return pdf_bytes

