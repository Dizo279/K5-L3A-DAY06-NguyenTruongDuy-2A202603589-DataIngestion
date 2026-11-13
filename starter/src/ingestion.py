"""Read and normalize source data while retaining page traceability."""
import unicodedata
from pathlib import Path

from pypdf import PdfReader

from .models import DocumentPage


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """Extract every physical page and retain its source metadata.

    Detect and record pages with no text. OCR, when needed, is a separate step.
    """
    reader = PdfReader(str(path))
    pages: list[DocumentPage] = []
    for page_number, pdf_page in enumerate(reader.pages, start=1):
        raw_text = pdf_page.extract_text() or ""
        text = normalize_text(raw_text)
        pages.append(
            DocumentPage(
                document_id=document_id,
                source=source,
                page=page_number,
                text=text,
                metadata={
                    "has_text": bool(text),
                    "physical_page": page_number,
                },
            )
        )
    return pages


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace while retaining line structure."""
    normalized = unicodedata.normalize("NFKC", text).replace("\u00a0", " ")
    lines = [" ".join(line.split()) for line in normalized.splitlines()]
    return "\n".join(line for line in lines if line).strip()
