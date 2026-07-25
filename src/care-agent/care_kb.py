"""Local care knowledge-base tool.

The Agent Bricks Knowledge Assistant could not be provisioned in this workspace
(managed ingestion failed twice with no surfaced error), so the 8 KB documents
are bundled with the harness and served through a small deterministic retrieval
tool instead. The docs are identical to the ones in the `care_kb` UC volume.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

from pydantic import Field

_KB_DIR = Path(__file__).resolve().parent / "kb_docs"
_WORD = re.compile(r"[a-z0-9][a-z0-9\-]+")


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _load_docs() -> list[tuple[str, str]]:
    return [(p.name, p.read_text(encoding="utf-8")) for p in sorted(_KB_DIR.glob("*.md"))]


def search_care_kb(
    query: Annotated[
        str,
        Field(
            description=(
                "What to look up in the care documentation: an alert code "
                "(SPO2-CRIT, BATT-LOW...), a symptom (disconnects, battery drain), "
                "or a policy topic (warranty, RMA, privacy, escalation)."
            )
        ),
    ],
) -> str:
    """Search Better2gether's care documentation (knowledge base).

    Covers: alert-code glossary, vitals interpretation, connectivity & sync
    troubleshooting (TS- procedures), firmware/OTA update SOP, device setup,
    warranty/RMA policy, data privacy, and the wellness program handbook.
    Returns the most relevant documents; always cite the doc filename.
    """
    _STOP = {
        "what", "does", "an", "a", "the", "and", "or", "is", "are", "to", "of",
        "in", "for", "on", "mean", "means", "should", "tell", "member", "alert",
        "alerts", "this", "that", "how", "why", "when", "with", "about",
    }
    docs = _load_docs()
    q_tokens = {t for t in _tokens(query) if t not in _STOP}
    if not q_tokens:
        return "Empty query. Available docs: " + ", ".join(name for name, _ in docs)

    scored: list[tuple[float, str, str]] = []
    for name, text in docs:
        doc_tokens = _tokens(text)
        if not doc_tokens:
            continue
        counts: dict[str, int] = {}
        for t in doc_tokens:
            counts[t] = counts.get(t, 0) + 1
        score = 0.0
        for t in q_tokens:
            tf = counts.get(t, 0)
            if not tf:
                continue
            # codes like spo2-crit, ts-04, v2.3.8 are the strongest signal
            weight = 5.0 if (re.search(r"\d", t) or "-" in t) else 1.0
            score += weight * tf
        score /= len(doc_tokens) ** 0.5
        if score > 0:
            scored.append((score, name, text))

    if not scored:
        return (
            "No care-KB document matched. Available docs: "
            + ", ".join(name for name, _ in docs)
        )

    scored.sort(reverse=True)
    top = scored[:2]
    parts = [f"=== {name} ===\n{text.strip()}" for _, name, text in top]
    return "\n\n".join(parts)
