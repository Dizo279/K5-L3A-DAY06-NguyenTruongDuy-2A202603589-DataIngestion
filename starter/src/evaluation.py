"""Evaluate retrieval evidence and preserve per-query traces."""
import re
from typing import Any


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Check source/page and evidence coverage for one benchmark question.

    Accept any documented alternative gold evidence. Do not infer human grounding
    or chunk coherence labels from exact string match.
    """
    gold_sources = _as_list(question.get("gold_source_id"))
    gold_pages = _as_list(question.get("gold_page"))
    quotes = _as_list(question.get("evidence_quote"))

    def is_hit(hit: dict[str, Any]) -> bool:
        source_ok = hit.get("document_id") in gold_sources or hit.get("source") in gold_sources
        page_ok = hit.get("page") in gold_pages
        if not (source_ok and page_ok):
            return False
        if not quotes:
            return True
        text = _normalize(hit.get("text", ""))
        return any(_normalize(quote) in text for quote in quotes if quote)

    hit_flags = [is_hit(hit) for hit in hits[:3]]
    return {
        "question_id": question.get("id"),
        "strategy": question.get("strategy", "unknown"),
        "split": question.get("split", "unknown"),
        "question": question.get("question", ""),
        "hit_at_1": bool(hit_flags and hit_flags[0]),
        "evidence_hit_at_3": any(hit_flags),
        "retrieved_chunk_ids": [hit.get("chunk_id") for hit in hits[:3]],
        "hits": hits[:3],
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by strategy and split."""
    summary: dict[str, dict[str, dict[str, int]]] = {}
    for trace in traces:
        strategy = trace.get("strategy", "unknown")
        split = trace.get("split", "unknown")
        bucket = summary.setdefault(strategy, {}).setdefault(
            split, {"count": 0, "hit_at_1": 0, "evidence_hit_at_3": 0}
        )
        bucket["count"] += 1
        bucket["hit_at_1"] += int(bool(trace.get("hit_at_1")))
        bucket["evidence_hit_at_3"] += int(bool(trace.get("evidence_hit_at_3")))
    return summary


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", str(value)).strip().casefold()
