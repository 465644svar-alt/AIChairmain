"""Pydantic models for request/response schemas."""

from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    query: str


class MemberResponse(BaseModel):
    member_id: str
    member_name: str
    provider: str
    model: str
    response: str
    error: Optional[str] = None


class PeerReview(BaseModel):
    reviewer_id: str
    reviewer_name: str
    rankings: list[dict]  # [{member_id, rank, reasoning}]


class SynthesisResponse(BaseModel):
    chairman_model: str
    synthesis: str


class CouncilSession(BaseModel):
    session_id: str
    query: str
    stage: str  # "responses" | "review" | "synthesis" | "complete"
    responses: list[MemberResponse] = []
    reviews: list[PeerReview] = []
    synthesis: Optional[SynthesisResponse] = None
