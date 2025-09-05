from __future__ import annotations

from pydantic import BaseModel, Field, conlist


class TemplateResponse(BaseModel):
    outline: str
    example: str
    bullet_points: conlist(str, min_length=3, max_length=5)  # type: ignore[type-arg]


class RefineResponse(BaseModel):
    refined: str
    improvement_hints: conlist(str, min_length=2, max_length=6)  # type: ignore[type-arg]


class Contradiction(BaseModel):
    self_idx: int
    peer_idx: int
    reason: str


class ConflictsResponse(BaseModel):
    duplicates: list[list[int]]
    contradictions: list[Contradiction]


class SummaryResponse(BaseModel):
    strengths: conlist(str, min_length=3, max_length=3)  # type: ignore[type-arg]
    areas_for_growth: conlist(str, min_length=3, max_length=3)  # type: ignore[type-arg]
    next_steps: conlist(str, min_length=3, max_length=3)  # type: ignore[type-arg]


