"""
services/ai_summarizer/summarizer.py
Uses LangChain + OpenAI to:
  1. Generate plain-English 3-sentence summaries for papers.
  2. Evaluate the relationship between two paper abstracts and return a
     correlation value (0–1) plus a relationship type label.
"""

from __future__ import annotations

import os
from typing import Literal

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseOutputParser
import re


RelationshipType = Literal["builds_on", "validates", "challenges", "unrelated"]

_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_TEMPERATURE = 0.2


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=_OPENAI_MODEL,
        temperature=_TEMPERATURE,
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )


# ---------------------------------------------------------------------------
# Plain-language summary
# ---------------------------------------------------------------------------

_SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a science communicator. Your job is to explain research papers "
                "to members of the public who have no scientific background. "
                "Keep your explanation to exactly 3 sentences."
            ),
        ),
        (
            "human",
            (
                "Title: {title}\n\n"
                "Abstract: {abstract}\n\n"
                "Write a plain-English summary of this paper in exactly 3 sentences."
            ),
        ),
    ]
)


async def generate_summary(title: str, abstract: str) -> str:
    """Return a 3-sentence plain-English summary of a paper."""
    chain = _SUMMARY_PROMPT | _llm()
    response = await chain.ainvoke({"title": title, "abstract": abstract})
    return response.content.strip()


# ---------------------------------------------------------------------------
# Relationship evaluation
# ---------------------------------------------------------------------------

_RELATIONSHIP_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are an expert research analyst. Given two paper abstracts, "
                "determine how Paper A relates to Paper B. "
                "Respond ONLY with a JSON object containing two keys:\n"
                '  "relationship": one of ["builds_on", "validates", "challenges", "unrelated"]\n'
                '  "correlation_value": a float between 0.0 and 1.0 '
                "(1.0 = extremely closely related, 0.0 = completely unrelated)."
            ),
        ),
        (
            "human",
            (
                "Paper A abstract:\n{abstract_a}\n\n"
                "Paper B abstract:\n{abstract_b}\n\n"
                "Evaluate the relationship."
            ),
        ),
    ]
)


class _RelationshipParser(BaseOutputParser):
    """Parse the LLM JSON response into a structured dict."""

    def parse(self, text: str) -> dict:
        import json

        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON substring
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                data = {"relationship": "unrelated", "correlation_value": 0.0}

        rel = data.get("relationship", "unrelated")
        if rel not in ("builds_on", "validates", "challenges", "unrelated"):
            rel = "unrelated"

        try:
            corr = float(data.get("correlation_value", 0.0))
            corr = max(0.0, min(1.0, corr))
        except (TypeError, ValueError):
            corr = 0.0

        return {"relationship": rel, "correlation_value": corr}


async def evaluate_relationship(
    abstract_a: str,
    abstract_b: str,
) -> dict:
    """
    Evaluate how Paper A relates to Paper B.

    Returns::

        {
            "relationship": "builds_on" | "validates" | "challenges" | "unrelated",
            "correlation_value": 0.0 – 1.0,
        }
    """
    chain = _RELATIONSHIP_PROMPT | _llm() | _RelationshipParser()
    return await chain.ainvoke(
        {"abstract_a": abstract_a, "abstract_b": abstract_b}
    )
