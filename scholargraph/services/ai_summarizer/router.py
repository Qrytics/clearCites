"""
services/ai_summarizer/router.py
FastAPI router exposing AI summarizer endpoints.
Mount this into the main graph_api app or run as a standalone service.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .summarizer import evaluate_relationship, generate_summary

router = APIRouter(prefix="/ai", tags=["AI"])


class SummaryRequest(BaseModel):
    title: str
    abstract: str


class RelationshipRequest(BaseModel):
    abstract_a: str
    abstract_b: str


@router.post("/summary")
async def summarize_paper(req: SummaryRequest):
    """Generate a plain-English 3-sentence summary for a paper."""
    try:
        summary = await generate_summary(req.title, req.abstract)
        return {"summary": summary}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/relationship")
async def relationship_endpoint(req: RelationshipRequest):
    """
    Evaluate how Paper A relates to Paper B.

    Returns the relationship type and a correlation value (0–1).
    """
    try:
        result = await evaluate_relationship(req.abstract_a, req.abstract_b)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
