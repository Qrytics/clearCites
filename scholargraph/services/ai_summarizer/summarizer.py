"""
services/ai_summarizer/summarizer.py
Local ML-based implementation – no external API or API key required.
  1. Extractive summarisation: scores sentences in the abstract using
     TF-IDF word weights and returns the top sentences in reading order.
  2. Relationship evaluation: TF-IDF cosine similarity for correlation
     value; keyword/phrase pattern matching for relationship type.
"""

from __future__ import annotations

import asyncio
import re
from typing import Literal

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


RelationshipType = Literal["builds_on", "validates", "challenges", "unrelated"]

# Regex that splits on sentence-ending punctuation followed by whitespace
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]


# ---------------------------------------------------------------------------
# Plain-language extractive summary (no API key required)
# ---------------------------------------------------------------------------

def _extractive_summary(title: str, abstract: str, n: int = 3) -> str:
    """Pick the *n* highest-scoring sentences from the abstract via TF-IDF."""
    sentences = _split_sentences(abstract)
    if not sentences:
        return abstract.strip()
    if len(sentences) <= n:
        return " ".join(sentences)

    try:
        vec = TfidfVectorizer(stop_words="english")
        tfidf = vec.fit_transform(sentences)
        # Score each sentence by the mean TF-IDF weight across its tokens
        scores = np.asarray(tfidf.mean(axis=1)).flatten()
    except ValueError:
        return " ".join(sentences[:n])

    # Restore the original reading order after selecting top-n
    top_indices = sorted(np.argsort(scores)[-n:])
    return " ".join(sentences[i] for i in top_indices)


async def generate_summary(title: str, abstract: str) -> str:
    """Return a 3-sentence extractive summary of a paper (no API key required)."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _extractive_summary, title, abstract, 3)


# ---------------------------------------------------------------------------
# Relationship evaluation – TF-IDF cosine similarity + keyword heuristics
# (no API key required)
# ---------------------------------------------------------------------------

_VALIDATES_RE = re.compile(
    r"\b(confirm[s]?|confirmed|validat\w*|verif\w*|support[s]?|replicate\w*|reproduc\w*)\b",
    re.I,
)
_CHALLENGES_RE = re.compile(
    r"\b(challeng\w*|contradict\w*|refut\w*|disput\w*|questions?|inconsistent|contrary)\b",
    re.I,
)
_BUILDS_ON_RE = re.compile(
    r"\b(extend[s]?|build[s]?\s+on|expand[s]?|improv\w*|enhanc\w*|novel|based\s+on)\b",
    re.I,
)

_SIMILARITY_THRESHOLD_UNRELATED = 0.08
_SIMILARITY_THRESHOLD_RELATED = 0.25


def _classify_relationship(
    abstract_a: str, abstract_b: str, similarity: float
) -> RelationshipType:
    """Keyword-pattern heuristic for relationship type."""
    if similarity < _SIMILARITY_THRESHOLD_UNRELATED:
        return "unrelated"

    combined = f"{abstract_a} {abstract_b}"
    val = len(_VALIDATES_RE.findall(combined))
    chal = len(_CHALLENGES_RE.findall(combined))
    build = len(_BUILDS_ON_RE.findall(combined))

    if val == 0 and chal == 0 and build == 0:
        return "builds_on" if similarity >= _SIMILARITY_THRESHOLD_RELATED else "unrelated"

    _SCORES: dict[RelationshipType, int] = {
        "validates": val,
        "challenges": chal,
        "builds_on": build,
    }
    return max(_SCORES, key=lambda k: _SCORES[k])


def _compute_relationship(abstract_a: str, abstract_b: str) -> dict:
    docs = [abstract_a or "", abstract_b or ""]
    if not any(d.strip() for d in docs):
        return {"relationship": "unrelated", "correlation_value": 0.0}

    try:
        vec = TfidfVectorizer(stop_words="english", min_df=1)
        tfidf = vec.fit_transform(docs)
        sim = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
    except ValueError:
        sim = 0.0

    sim = max(0.0, min(1.0, sim))
    rel = _classify_relationship(abstract_a, abstract_b, sim)
    return {"relationship": rel, "correlation_value": round(sim, 4)}


async def evaluate_relationship(abstract_a: str, abstract_b: str) -> dict:
    """
    Evaluate how Paper A relates to Paper B.

    Uses TF-IDF cosine similarity for correlation and keyword heuristics
    for relationship type classification. No external API or API key required.

    Returns::

        {
            "relationship": "builds_on" | "validates" | "challenges" | "unrelated",
            "correlation_value": 0.0 – 1.0,
        }
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _compute_relationship, abstract_a, abstract_b)
