"""
routes_documents.py
===================
FastAPI router for the Bilingual Legal Document Drafter.

POST /api/documents/draft
  Body: { template_type, party_details, language }
  Returns: application/pdf
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

logger = logging.getLogger("agent_forge.routes_documents")

router = APIRouter()


class DraftRequest(BaseModel):
    template_type: str = Field(..., description="Template key: mutual_divorce_petition | protection_order_application | maintenance_application | rcr_notice")
    party_details: dict[str, Any] = Field(default_factory=dict, description="Dynamic form field values")
    language: str = Field(default="en", description="Vernacular language code: en / hi / kn / te / ta / bn / mr / gu / ml / ur")


VALID_TEMPLATES = {
    "mutual_divorce_petition",
    "protection_order_application",
    "maintenance_application",
    "rcr_notice",
}

VALID_LANGUAGES = {"en", "hi", "kn", "te", "ta", "bn", "mr", "gu", "ml", "ur"}


@router.post("/documents/draft", tags=["Documents"])
async def draft_document(req: DraftRequest) -> Response:
    """
    Generate a bilingual legal PDF document.

    Returns the PDF as an inline binary response with content-type application/pdf.
    """
    if req.template_type not in VALID_TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid template_type '{req.template_type}'. Valid options: {sorted(VALID_TEMPLATES)}",
        )

    lang = req.language.lower() if req.language else "en"
    if lang not in VALID_LANGUAGES:
        lang = "en"  # graceful fallback

    try:
        from app.services.document_drafter import generate_legal_document_pdf

        pdf_bytes = generate_legal_document_pdf(
            template_type=req.template_type,
            party_details=req.party_details,
            language=lang,
        )
    except ImportError as e:
        logger.error(f"reportlab not installed: {e}")
        raise HTTPException(
            status_code=503,
            detail="PDF generation service unavailable. reportlab is not installed on the server.",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    filename = f"{req.template_type}_{lang}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
