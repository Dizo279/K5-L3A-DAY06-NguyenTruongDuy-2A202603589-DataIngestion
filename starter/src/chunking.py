"""Implement fixed-size and structure-aware chunking."""
import re

from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    """Split text into overlapping character windows."""
    if size <= 0:
        raise ValueError("size must be greater than zero")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be between zero and size - 1")

    text = page.text.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    step = size - overlap
    for index, start in enumerate(range(0, len(text), step)):
        chunk_text = text[start:start + size]
        if not chunk_text:
            break
        chunks.append(
            Chunk(
                chunk_id=f"{page.document_id}-p{page.page}-fixed-{index:04d}",
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=chunk_text,
                metadata=dict(page.metadata),
            )
        )
        if start + size >= len(text):
            break
    return chunks


def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    """Group paragraphs until ``max_size`` and split oversized blocks."""
    if max_size <= 0:
        raise ValueError("max_size must be greater than zero")

    text = page.text.strip()
    if not text:
        return []

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]
    units: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_size:
            if current:
                units.append(current)
                current = ""
            units.extend(
                paragraph[start:start + max_size]
                for start in range(0, len(paragraph), max_size)
            )
        elif not current:
            current = paragraph
        elif len(current) + 2 + len(paragraph) <= max_size:
            current = f"{current}\n\n{paragraph}"
        else:
            units.append(current)
            current = paragraph
    if current:
        units.append(current)

    return [
        Chunk(
            chunk_id=f"{page.document_id}-p{page.page}-paragraph-{index:04d}",
            document_id=page.document_id,
            source=page.source,
            page=page.page,
            text=chunk_text,
            metadata=dict(page.metadata),
        )
        for index, chunk_text in enumerate(units)
    ]
