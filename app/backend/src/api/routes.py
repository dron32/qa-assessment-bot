from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from ..core.auth import CurrentUser, get_current_user, require_admin
from ..llm.client import LlmClient
from ..tasks.integration import task_manager

router = APIRouter(prefix="/api")


@router.post("/reviews/self/start")
async def start_self_review(user: CurrentUser = Depends(get_current_user)) -> dict:
    return {"review_id": 1, "type": "self", "author_id": user.id, "subject_id": user.id}


@router.post("/reviews/peer/start")
async def start_peer_review(subject_id: int, user: CurrentUser = Depends(get_current_user)) -> dict:
    return {"review_id": 2, "type": "peer", "author_id": user.id, "subject_id": subject_id}


@router.post("/reviews/{review_id}/entry")
async def upsert_entry(review_id: int, competency_id: int, raw_text: str) -> dict:
    return {"id": 1, "review_id": review_id, "competency_id": competency_id, "raw_text": raw_text}


@router.post("/reviews/{review_id}/refine")
async def refine_review(review_id: int, text: str, user: CurrentUser = Depends(get_current_user)) -> dict:
    llm = LlmClient()
    out = llm.refine_text(text=text, trace_id=f"rev-{review_id}-u-{user.id}")
    return out.model_dump()


@router.post("/reviews/{review_id}/detect_conflicts")
async def detect_conflicts(review_id: int, self_items: list[str], peer_items: list[str]) -> dict:
    llm = LlmClient()
    out = llm.detect_conflicts(self_items=self_items, peer_items=peer_items, trace_id=f"rev-{review_id}")
    return out.model_dump()


@router.post("/summaries/{user_id}/generate")
async def generate_summary(user_id: int, cycle_id: int | None = None, user: CurrentUser = Depends(require_admin)) -> dict:
    """Генерация summary с запуском фоновой задачи."""
    return task_manager.start_summary_generation(user_id, cycle_id)

@router.post("/summaries/batch/generate")
async def generate_batch_summaries(user_ids: List[int], cycle_id: int | None = None, user: CurrentUser = Depends(require_admin)) -> dict:
    """Массовая генерация summary."""
    return task_manager.start_batch_summary_generation(user_ids, cycle_id)


# Admin CRUD заглушки с RBAC
@router.post("/admin/competencies", dependencies=[Depends(require_admin)])
async def create_competency(key: str, title: str) -> dict:
    return {"id": 1, "key": key, "title": title}


@router.post("/admin/templates", dependencies=[Depends(require_admin)])
async def create_template(competency_id: int, language: str, content: str) -> dict:
    return {"id": 1, "competency_id": competency_id, "language": language, "content": content}


@router.post("/admin/review_cycles", dependencies=[Depends(require_admin)])
async def create_cycle(title: str) -> dict:
    return {"id": 1, "title": title}


@router.post("/admin/users", dependencies=[Depends(require_admin)])
async def create_user(handle: str, email: str, role: str = "user") -> dict:
    return {"id": 1, "handle": handle, "email": email, "role": role}


# Эндпоинты для управления фоновыми задачами
@router.post("/tasks/reviews/{review_id}/compare")
async def start_review_comparison(review_id: int, user: CurrentUser = Depends(require_admin)) -> dict:
    """Запуск сравнения review."""
    return task_manager.start_review_comparison(review_id)

@router.post("/tasks/reviews/batch/compare")
async def start_batch_review_comparison(review_ids: List[int], user: CurrentUser = Depends(require_admin)) -> dict:
    """Массовое сравнение reviews."""
    return task_manager.start_batch_review_comparison(review_ids)

@router.post("/tasks/embeddings/generate")
async def start_embeddings_generation(text: str, model: str = "text-embedding-3-small", user: CurrentUser = Depends(require_admin)) -> dict:
    """Запуск генерации эмбеддингов."""
    return task_manager.start_embeddings_generation(text, model)

@router.post("/tasks/templates/cache")
async def start_templates_caching(template_ids: Optional[List[int]] = None, user: CurrentUser = Depends(require_admin)) -> dict:
    """Запуск кэширования шаблонов."""
    return task_manager.start_templates_caching(template_ids)

@router.post("/tasks/embeddings/warmup")
async def start_embeddings_cache_warmup(user: CurrentUser = Depends(require_admin)) -> dict:
    """Запуск прогрева кэша эмбеддингов."""
    return task_manager.start_embeddings_cache_warmup()

@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str, user: CurrentUser = Depends(require_admin)) -> dict:
    """Получение статуса задачи."""
    return task_manager.get_task_status(task_id)

@router.get("/tasks/metrics")
async def get_task_metrics(user: CurrentUser = Depends(require_admin)) -> dict:
    """Получение метрик выполнения задач."""
    return task_manager.get_task_metrics()


