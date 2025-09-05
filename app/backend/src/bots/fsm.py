from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ReviewState(Enum):
    IDLE = "idle"
    START = "start"
    SELECTING_CYCLE = "selecting_cycle"
    COLLECTING_ANSWERS = "collecting_answers"
    ANSWERING_COMPETENCIES = "answering_competencies"
    PREVIEW = "preview"
    REFINING = "refining"
    SUBMITTED = "submitted"


@dataclass
class ReviewSession:
    user_id: str
    platform: str  # "slack" | "telegram"
    review_type: str  # "self" | "peer"
    subject_id: Optional[str] = None
    cycle_id: Optional[int] = None
    state: ReviewState = ReviewState.IDLE
    answers: Dict[str, str] = None  # competency_id -> text
    review_id: Optional[int] = None
    
    def __post_init__(self):
        if self.answers is None:
            self.answers = {}


class FSMStore:
    """In-memory store for FSM sessions (в продакшене - Redis)"""
    
    def __init__(self):
        self._sessions: Dict[str, ReviewSession] = {}
    
    def get_session(self, user_id: str, platform: str) -> Optional[ReviewSession]:
        key = f"{platform}:{user_id}"
        return self._sessions.get(key)
    
    def save_session(self, session: ReviewSession) -> None:
        key = f"{session.platform}:{session.user_id}"
        self._sessions[key] = session
    
    def clear_session(self, user_id: str, platform: str) -> None:
        key = f"{platform}:{user_id}"
        self._sessions.pop(key, None)


# Глобальный store (в продакшене - DI)
fsm_store = FSMStore()
