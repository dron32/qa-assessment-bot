from pydantic import BaseModel
from typing import Optional


class CompetencyCreate(BaseModel):
    key: str
    title: str
    description: Optional[str] = ""


class CompetencyUpdate(BaseModel):
    key: str
    title: str
    description: Optional[str] = ""


class TemplateCreate(BaseModel):
    competency_id: int
    language: str
    content: str


class TemplateUpdate(BaseModel):
    competency_id: int
    language: str
    content: str


class UserCreate(BaseModel):
    handle: str
    email: str
    role: str = "user"


class UserUpdate(BaseModel):
    handle: str
    email: str
    role: str = "user"


class ReviewCycleCreate(BaseModel):
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ReviewCycleUpdate(BaseModel):
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
