from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Language = Literal["fr", "tn_ar", "tn_latn", "en"]
Status = Literal[
    "complete",
    "awaiting_clarification",
    "awaiting_confirmation",
    "cancelled",
    "unsupported",
]


class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    conversation_id: str | None = Field(default=None, max_length=100)


class ClassifierRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class ClassifierCandidate(BaseModel):
    intent: str
    probability: float = Field(ge=0, le=1)


class ClassifierResponse(BaseModel):
    candidates: list[ClassifierCandidate]
    model: str = "public-char-word-ngram-logistic-v1"
    training_data: str = "synthetic"


class RouteDecision(BaseModel):
    intent: str
    confidence: float = Field(ge=0, le=1)
    language: Language
    vehicle_id: int | None = None
    evidence: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    conversation_id: str
    status: Status
    reply: str
    route: RouteDecision
    data: dict[str, Any] | list[dict[str, Any]] | None = None


class SessionState(BaseModel):
    pending_intent: str | None = None
    pending_vehicle_id: int | None = None
    pending_confirmation: bool = False
    last_vehicle_id: int | None = None
