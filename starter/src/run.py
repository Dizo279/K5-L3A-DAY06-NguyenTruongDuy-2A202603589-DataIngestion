"""Run the Day 06 ingestion, retrieval, and evaluation pipeline."""
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .chunking import by_paragraph, fixed_size
from .embeddings import MyEmbedder
from .evaluation import evaluate_query, summarize
from .ingestion import load_pdf
from .models import Chunk, DocumentPage
from .store import PgVectorStore

BASE_DIR = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _section_for_page(text: str, current: str) -> str:
    headings = {
        "executive summary": "Executive Summary",
        "energy": "Energy",
        "metals": "Metals",
        "agriculture": "Agriculture",
        "precious metals": "Precious Metals",
        "fertilizers": "Fertilizers",
        "special focus": "Special Focus",
    }
    first_line = " ".join(next((line for line in text.splitlines() if line.strip()), "").casefold().split())
    for key, value in headings.items():
        if first_line.startswith(key):
            return value
    return current


def _add_metadata(pages: list[DocumentPage], manifest: dict[str, Any]) -> list[DocumentPage]:
    year = manifest.get("metadata_fields", {}).get("year", {}).get("value", 2026)
    section = "Executive Summary"
    for page in pages:
        section = _section_for_page(page.text, section)
        page.metadata.update({"section": section, "year": year})
    return pages


def _embed_batches(embedder: MyEmbedder, texts: list[str], batch_size: int = 64) -> list[list[float]]:
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        vectors.extend(embedder.embed_documents(texts[start:start + batch_size]))
    return vectors


def _build_chunks(pages: list[DocumentPage]) -> dict[str, list[Chunk]]:
    fixed = [chunk for page in pages for chunk in fixed_size(page, size=500, overlap=50)]
    paragraph = [chunk for page in pages for chunk in by_paragraph(page, max_size=1000)]
    return {"A": fixed, "B": paragraph, "C": paragraph}


def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    manifest_items = _read_json(BASE_DIR / "data" / "manifest.json")
    questions = _read_json(BASE_DIR / "benchmark" / "questions.json")
    if not manifest_items:
        raise ValueError("data/manifest.json is empty")
    if len(questions) < 20:
        raise ValueError("benchmark must contain at least 20 questions")

    manifest = manifest_items[0]
    pdf_path = BASE_DIR / manifest["source_path_or_url"]
    pages = load_pdf(pdf_path, manifest["source_id"], manifest["source_path_or_url"])
    pages = _add_metadata(pages, manifest)
    content_pages = [page for page in pages if page.text]
    if len(content_pages) < 30:
        raise ValueError(f"expected at least 30 non-empty content pages, got {len(content_pages)}")

    model_name = os.getenv("EMBEDDING_MODEL", "")
    database_url = os.getenv("DATABASE_URL", "")
    embedder = MyEmbedder(model_name)
    store = PgVectorStore(database_url, embedder.dimensions)
    store.create_schema()

    strategies = _build_chunks(pages)
    vectors_by_strategy: dict[str, list[list[float]]] = {}
    for strategy in ("A", "B"):
        chunks = strategies[strategy]
        vectors = _embed_batches(embedder, [chunk.text for chunk in chunks])
        store.upsert(strategy, chunks, vectors)
        vectors_by_strategy[strategy] = vectors
    store.upsert("C", strategies["C"], vectors_by_strategy["B"])

    traces: list[dict[str, Any]] = []
    query_vectors = _embed_batches(embedder, [question["question"] for question in questions])
    for strategy in ("A", "B", "C"):
        for question, query_vector in zip(questions, query_vectors):
            filters = question.get("filter", {}) if strategy == "C" else {}
            hits = store.search(strategy, query_vector, top_k=3, filters=filters)
            trace = evaluate_query({**question, "strategy": strategy}, hits)
            traces.append(trace)

    results_dir = BASE_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2), encoding="utf-8")
    (results_dir / "summary.json").write_text(
        json.dumps(summarize(traces), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summarize(traces), ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
