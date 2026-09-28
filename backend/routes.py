"""
Backend/routes.py

Defines the DocumentRequest model, the Gemini-powered generator, and
the /generate + /health endpoints.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

router = APIRouter()


class GeminiDocumentGenerator:
    """Generates legal document text using Google's Gemini model."""

    def __init__(self, model_name: str = None):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY not found. Set it in your .env file."
            )
        genai.configure(api_key=api_key)
        self.model_name = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")
        self.model = genai.GenerativeModel(self.model_name)

    def _build_prompt(self, document_type: str, parties: str, terms: str, dates: str) -> str:
        return (
            "You are an expert legal drafter. Generate a comprehensive, formally "
            f"structured legal document titled '{document_type}'.\n\n"
            f"Involved parties: {parties}\n"
            f"Effective Date: {dates}\n"
            f"Terms and conditions to include: {terms}\n\n"
            "Requirements:\n"
            "- Open with a short preamble identifying the parties and purpose.\n"
            "- Organize the body into clearly numbered sections appropriate for "
            "this document type (Services, Term and Termination, Payment, "
            "Confidentiality, Governing Law, Entire Agreement, Severability, etc.), "
            "including only the sections that make sense for this document type.\n"
            "- Weave the terms and conditions into the relevant sections rather "
            "than repeating them verbatim as a list.\n"
            "- Close with a signature block listing every named party.\n"
            "- Use plain, professional legal English. Return only the finished "
            "document text, using '#' for the main title and '##' for section "
            "headings. No AI disclaimers, no markdown code fences.\n"
        )

    def generate_document(self, document_type: str, parties: str, terms: str, dates: str) -> str:
        prompt = self._build_prompt(document_type, parties, terms, dates)
        try:
            response = self.model.generate_content(prompt)
        except Exception as exc:
            raise RuntimeError(f"Gemini generation failed: {exc}") from exc

        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned an empty response.")
        return text


# Initialize once at import time. If the key is missing, the server still
# starts -- /generate will return a clear 500 instead of crashing on boot.
_init_error = None
try:
    gemini_generator = GeminiDocumentGenerator()
except EnvironmentError as exc:
    gemini_generator = None
    _init_error = str(exc)


class DocumentRequest(BaseModel):
    document_type: str = Field(..., min_length=1, examples=["Freelance Work Contract"])
    parties: str = Field(..., min_length=1, examples=["Jane Doe (Service Provider), TechNova Inc. (Client)"])
    terms: str = Field(..., min_length=1, examples=["Payment within 30 days; Confidentiality maintained"])
    dates: str = Field(..., min_length=1, examples=["April 15, 2025"])


@router.post("/generate")
def generate_legal_document(request: DocumentRequest):
    if gemini_generator is None:
        raise HTTPException(
            status_code=500,
            detail=f"AI generator is not configured: {_init_error}",
        )
    try:
        document_text = gemini_generator.generate_document(
            request.document_type,
            request.parties,
            request.terms,
            request.dates,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"document": document_text}


@router.get("/health")
def health_check():
    return {"status": "ok", "ai_ready": gemini_generator is not None}