from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any
import uuid


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


@dataclass
class LLMResult:
    provider: str
    model: str
    content: str | None
    error: str | None
    latency_ms: int
    raw: dict[str, Any] | None = None


@dataclass
class Stage1Result:
    question: str
    responses: list[LLMResult]


@dataclass
class Stage2Review:
    reviewer_provider: str
    reviewer_model: str
    review_text: str | None
    ranking: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class AggregateRanking:
    label_to_model: dict[str, str]
    average_ranks: dict[str, float]
    aggregate_order: list[str]


@dataclass
class Stage2Result:
    reviews: list[Stage2Review]
    aggregate: AggregateRanking


@dataclass
class Stage3Result:
    content: str | None
    error: str | None
    used_fallback: bool = False


@dataclass
class ConversationNode:
    id: str
    parent_id: str | None
    role: str
    content: str
    created_at: str = field(default_factory=utc_now_iso)
    stage_data: dict[str, Any] | None = None

    @staticmethod
    def new(role: str, content: str, parent_id: str | None = None, stage_data: dict[str, Any] | None = None) -> "ConversationNode":
        return ConversationNode(id=str(uuid.uuid4()), parent_id=parent_id, role=role, content=content, stage_data=stage_data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
