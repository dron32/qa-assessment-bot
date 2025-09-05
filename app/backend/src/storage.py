"""
Простое in-memory хранилище для демонстрации.
В продакшене должно быть заменено на реальную БД.
"""

from typing import Dict, List, Optional
from datetime import datetime

# In-memory хранилище
_competencies: Dict[int, dict] = {
    1: {"id": 1, "key": "skill1", "title": "Skill 1", "description": "", "is_active": True}
}

_templates: Dict[int, dict] = {
    1: {"id": 1, "competency_id": 1, "language": "ru", "content": "Шаблон ответа"}
}

_users: Dict[int, dict] = {
    1: {"id": 1, "handle": "admin", "email": "admin@example.com", "role": "admin"}
}

_review_cycles: Dict[int, dict] = {
    1: {"id": 1, "title": "Q1 2024", "start_date": "2024-01-01", "end_date": "2024-03-31", "is_active": True}
}

_next_id = 2


def get_next_id() -> int:
    """Получить следующий ID."""
    global _next_id
    current_id = _next_id
    _next_id += 1
    return current_id


# Competencies
def get_competencies() -> List[dict]:
    """Получить все компетенции."""
    return list(_competencies.values())


def create_competency(key: str, title: str, description: str = "") -> dict:
    """Создать новую компетенцию."""
    competency_id = get_next_id()
    competency = {
        "id": competency_id,
        "key": key,
        "title": title,
        "description": description,
        "is_active": True
    }
    _competencies[competency_id] = competency
    return competency


def update_competency(competency_id: int, key: str, title: str, description: str = "") -> Optional[dict]:
    """Обновить компетенцию."""
    if competency_id not in _competencies:
        return None
    
    _competencies[competency_id].update({
        "key": key,
        "title": title,
        "description": description
    })
    return _competencies[competency_id]


def delete_competency(competency_id: int) -> bool:
    """Удалить компетенцию."""
    if competency_id in _competencies:
        del _competencies[competency_id]
        return True
    return False


# Templates
def get_templates() -> List[dict]:
    """Получить все шаблоны."""
    return list(_templates.values())


def create_template(competency_id: int, language: str, content: str) -> dict:
    """Создать новый шаблон."""
    template_id = get_next_id()
    template = {
        "id": template_id,
        "competency_id": competency_id,
        "language": language,
        "content": content
    }
    _templates[template_id] = template
    return template


def update_template(template_id: int, competency_id: int, language: str, content: str) -> Optional[dict]:
    """Обновить шаблон."""
    if template_id not in _templates:
        return None
    
    _templates[template_id].update({
        "competency_id": competency_id,
        "language": language,
        "content": content
    })
    return _templates[template_id]


def delete_template(template_id: int) -> bool:
    """Удалить шаблон."""
    if template_id in _templates:
        del _templates[template_id]
        return True
    return False


# Users
def get_users() -> List[dict]:
    """Получить всех пользователей."""
    return list(_users.values())


def create_user(handle: str, email: str, role: str = "user") -> dict:
    """Создать нового пользователя."""
    user_id = get_next_id()
    user = {
        "id": user_id,
        "handle": handle,
        "email": email,
        "role": role
    }
    _users[user_id] = user
    return user


def update_user(user_id: int, handle: str, email: str, role: str = "user") -> Optional[dict]:
    """Обновить пользователя."""
    if user_id not in _users:
        return None
    
    _users[user_id].update({
        "handle": handle,
        "email": email,
        "role": role
    })
    return _users[user_id]


def delete_user(user_id: int) -> bool:
    """Удалить пользователя."""
    if user_id in _users:
        del _users[user_id]
        return True
    return False


# Review Cycles
def get_review_cycles() -> List[dict]:
    """Получить все циклы ревью."""
    return list(_review_cycles.values())


def create_review_cycle(title: str, start_date: str = None, end_date: str = None) -> dict:
    """Создать новый цикл ревью."""
    cycle_id = get_next_id()
    cycle = {
        "id": cycle_id,
        "title": title,
        "start_date": start_date,
        "end_date": end_date,
        "is_active": True
    }
    _review_cycles[cycle_id] = cycle
    return cycle


def update_review_cycle(cycle_id: int, title: str, start_date: str = None, end_date: str = None) -> Optional[dict]:
    """Обновить цикл ревью."""
    if cycle_id not in _review_cycles:
        return None
    
    _review_cycles[cycle_id].update({
        "title": title,
        "start_date": start_date,
        "end_date": end_date
    })
    return _review_cycles[cycle_id]


def delete_review_cycle(cycle_id: int) -> bool:
    """Удалить цикл ревью."""
    if cycle_id in _review_cycles:
        del _review_cycles[cycle_id]
        return True
    return False
