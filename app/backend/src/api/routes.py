from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from ..core.auth import CurrentUser, get_current_user, require_admin
from ..llm.client import LlmClient
from ..tasks.integration import task_manager
from ..domain.services import (
    user_service, review_service, competency_service, template_service
)
from ..schemas.admin import (
    CompetencyCreate, CompetencyUpdate,
    TemplateCreate, TemplateUpdate,
    UserCreate, UserUpdate,
    ReviewCycleCreate, ReviewCycleUpdate
)
from ..storage import (
    get_competencies, create_competency, update_competency, delete_competency,
    get_templates, create_template, update_template, delete_template,
    get_users, create_user, update_user, delete_user,
    get_review_cycles, create_review_cycle, update_review_cycle, delete_review_cycle
)

router = APIRouter()

# Глобальные экземпляры сервисов для тестирования
llm_client = LlmClient()


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


# Admin CRUD с RBAC
@router.get("/admin/competencies", dependencies=[Depends(require_admin)])
async def get_competencies_endpoint() -> dict:
    return {"competencies": get_competencies()}

@router.post("/admin/competencies", dependencies=[Depends(require_admin)])
async def create_competency_endpoint(data: CompetencyCreate) -> dict:
    return create_competency(data.key, data.title, data.description)

@router.put("/admin/competencies/{competency_id}", dependencies=[Depends(require_admin)])
async def update_competency_endpoint(competency_id: int, data: CompetencyUpdate) -> dict:
    result = update_competency(competency_id, data.key, data.title, data.description)
    if result is None:
        raise HTTPException(status_code=404, detail="Competency not found")
    return result

@router.delete("/admin/competencies/{competency_id}", dependencies=[Depends(require_admin)])
async def delete_competency_endpoint(competency_id: int) -> dict:
    if not delete_competency(competency_id):
        raise HTTPException(status_code=404, detail="Competency not found")
    return {"message": "Competency deleted", "id": competency_id}


@router.get("/admin/templates", dependencies=[Depends(require_admin)])
async def get_templates_endpoint() -> dict:
    return {"templates": get_templates()}

@router.post("/admin/templates", dependencies=[Depends(require_admin)])
async def create_template_endpoint(data: TemplateCreate) -> dict:
    return create_template(data.competency_id, data.language, data.content)

@router.put("/admin/templates/{template_id}", dependencies=[Depends(require_admin)])
async def update_template_endpoint(template_id: int, data: TemplateUpdate) -> dict:
    result = update_template(template_id, data.competency_id, data.language, data.content)
    if result is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return result

@router.delete("/admin/templates/{template_id}", dependencies=[Depends(require_admin)])
async def delete_template_endpoint(template_id: int) -> dict:
    if not delete_template(template_id):
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted", "id": template_id}


@router.get("/admin/review_cycles", dependencies=[Depends(require_admin)])
async def get_review_cycles_endpoint() -> dict:
    return {"cycles": get_review_cycles()}

@router.post("/admin/review_cycles", dependencies=[Depends(require_admin)])
async def create_cycle_endpoint(data: ReviewCycleCreate) -> dict:
    return create_review_cycle(data.title, data.start_date, data.end_date)

@router.put("/admin/review_cycles/{cycle_id}", dependencies=[Depends(require_admin)])
async def update_cycle_endpoint(cycle_id: int, data: ReviewCycleUpdate) -> dict:
    result = update_review_cycle(cycle_id, data.title, data.start_date, data.end_date)
    if result is None:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    return result

@router.delete("/admin/review_cycles/{cycle_id}", dependencies=[Depends(require_admin)])
async def delete_cycle_endpoint(cycle_id: int) -> dict:
    if not delete_review_cycle(cycle_id):
        raise HTTPException(status_code=404, detail="Review cycle not found")
    return {"message": "Review cycle deleted", "id": cycle_id}


@router.get("/admin/users", dependencies=[Depends(require_admin)])
async def get_users_endpoint() -> dict:
    return {"users": get_users()}

@router.post("/admin/users", dependencies=[Depends(require_admin)])
async def create_user_endpoint(data: UserCreate) -> dict:
    return create_user(data.handle, data.email, data.role)

@router.put("/admin/users/{user_id}", dependencies=[Depends(require_admin)])
async def update_user_endpoint(user_id: int, data: UserUpdate) -> dict:
    result = update_user(user_id, data.handle, data.email, data.role)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result

@router.delete("/admin/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user_endpoint(user_id: int) -> dict:
    if not delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted", "id": user_id}


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


