"""Доменные модели для QA Assessment."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """Роли пользователей."""
    USER = "user"
    ADMIN = "admin"


class ReviewType(str, Enum):
    """Типы ревью."""
    SELF = "self"
    PEER = "peer"


class ReviewStatus(str, Enum):
    """Статусы ревью."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SUBMITTED = "submitted"


class Platform(str, Enum):
    """Платформы."""
    SLACK = "slack"
    TELEGRAM = "telegram"
    WEB = "web"


class User(BaseModel):
    """Пользователь."""
    id: int
    handle: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    role: UserRole = UserRole.USER
    platform: Platform
    created_at: datetime
    updated_at: datetime


class Competency(BaseModel):
    """Компетенция."""
    id: int
    key: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class ReviewCycle(BaseModel):
    """Цикл ревью."""
    id: int
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class Review(BaseModel):
    """Ревью."""
    id: int
    user_id: int
    cycle_id: int
    review_type: ReviewType
    status: ReviewStatus = ReviewStatus.DRAFT
    platform: Platform
    created_at: datetime
    updated_at: datetime


class ReviewEntry(BaseModel):
    """Запись в ревью."""
    id: int
    review_id: int
    competency_id: int
    answer: str = Field(..., min_length=1)
    score: int = Field(..., ge=1, le=5)
    created_at: datetime
    updated_at: datetime


class Summary(BaseModel):
    """Сводка по ревью."""
    id: int
    user_id: int
    cycle_id: int
    strengths: List[str]
    areas_for_growth: List[str]
    next_steps: List[str]
    generated_at: datetime
    created_at: datetime
    updated_at: datetime


class Template(BaseModel):
    """Шаблон ответа."""
    id: int
    competency_id: int
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
