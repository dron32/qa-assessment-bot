from __future__ import annotations

from pydantic import BaseModel, Field, conlist


class TemplateResponse(BaseModel):
    outline: str
    example: str
    bullet_points: conlist(str, min_length=3, max_length=5)  # type: ignore[type-arg]


class RefineResponse(BaseModel):
    refined: str
    improvement_hints: conlist(str, min_length=2, max_length=6)  # type: ignore[type-arg]


class Duplicate(BaseModel):
    self_item: str
    peer_item: str
    similarity: float


class Contradiction(BaseModel):
    self_item: str
    peer_item: str
    competency: str


class ConflictsResponse(BaseModel):
    duplicates: list[Duplicate]
    contradictions: list[Contradiction]


class SummaryResponse(BaseModel):
    strengths: list[str]
    areas_for_growth: list[str]
    next_steps: list[str]


