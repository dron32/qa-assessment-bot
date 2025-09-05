"""Доменные сервисы для QA Assessment."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from ..core.logging import get_logger
from .models import (
    User, Competency, ReviewCycle, Review, ReviewEntry, 
    Summary, Template, UserRole, ReviewType, ReviewStatus, Platform
)

logger = get_logger(__name__)


class UserService:
    """Сервис для работы с пользователями."""
    
    def __init__(self):
        self.logger = logger
    
    def create_user(
        self, 
        handle: str, 
        email: str, 
        role: UserRole = UserRole.USER,
        platform: Platform = Platform.WEB
    ) -> User:
        """Создание пользователя."""
        self.logger.info(
            "user_creation_started",
            action="create_user",
            handle=handle,
            email=email,
            role=role.value,
            platform=platform.value
        )
        
        # Валидация
        if not handle or len(handle.strip()) == 0:
            raise ValueError("Handle не может быть пустым")
        
        if not email or "@" not in email:
            raise ValueError("Некорректный email")
        
        # Создание пользователя (заглушка)
        user = User(
            id=1,  # В реальности будет из БД
            handle=handle.strip(),
            email=email.lower().strip(),
            role=role,
            platform=platform,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.logger.info(
            "user_created",
            action="create_user",
            user_id=user.id,
            handle=user.handle
        )
        
        return user
    
    def get_user_by_handle(self, handle: str) -> Optional[User]:
        """Получение пользователя по handle."""
        self.logger.info(
            "user_lookup",
            action="get_user_by_handle",
            handle=handle
        )
        
        # Заглушка - в реальности запрос к БД
        if handle == "admin":
            return User(
                id=1,
                handle="admin",
                email="admin@example.com",
                role=UserRole.ADMIN,
                platform=Platform.WEB,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        return None
    
    def is_admin(self, user: User) -> bool:
        """Проверка, является ли пользователь админом."""
        return user.role == UserRole.ADMIN


class CompetencyService:
    """Сервис для работы с компетенциями."""
    
    def __init__(self):
        self.logger = logger
    
    def create_competency(
        self, 
        key: str, 
        title: str, 
        description: Optional[str] = None
    ) -> Competency:
        """Создание компетенции."""
        self.logger.info(
            "competency_creation_started",
            action="create_competency",
            key=key,
            title=title
        )
        
        # Валидация
        if not key or len(key.strip()) == 0:
            raise ValueError("Key не может быть пустым")
        
        if not title or len(title.strip()) == 0:
            raise ValueError("Title не может быть пустым")
        
        competency = Competency(
            id=1,  # В реальности будет из БД
            key=key.strip().lower(),
            title=title.strip(),
            description=description.strip() if description else None,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.logger.info(
            "competency_created",
            action="create_competency",
            competency_id=competency.id,
            key=competency.key
        )
        
        return competency
    
    def get_active_competencies(self) -> List[Competency]:
        """Получение активных компетенций."""
        self.logger.info(
            "competencies_lookup",
            action="get_active_competencies"
        )
        
        # Заглушка - в реальности запрос к БД
        return [
            Competency(
                id=1,
                key="analytical_thinking",
                title="Аналитическое мышление",
                description="Способность анализировать проблемы и находить решения",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Competency(
                id=2,
                key="bug_reports",
                title="Написание баг-репортов",
                description="Качество и детальность баг-репортов",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]


class ReviewService:
    """Сервис для работы с ревью."""
    
    def __init__(self):
        self.logger = logger
    
    def start_review(
        self, 
        user_id: int, 
        cycle_id: int, 
        review_type: ReviewType,
        platform: Platform = Platform.WEB
    ) -> Review:
        """Начало ревью."""
        self.logger.info(
            "review_started",
            action="start_review",
            user_id=user_id,
            cycle_id=cycle_id,
            review_type=review_type.value,
            platform=platform.value
        )
        
        # Валидация
        if user_id <= 0:
            raise ValueError("Некорректный user_id")
        
        if cycle_id <= 0:
            raise ValueError("Некорректный cycle_id")
        
        review = Review(
            id=1,  # В реальности будет из БД
            user_id=user_id,
            cycle_id=cycle_id,
            review_type=review_type,
            status=ReviewStatus.DRAFT,
            platform=platform,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.logger.info(
            "review_created",
            action="start_review",
            review_id=review.id,
            user_id=user_id
        )
        
        return review
    
    def add_review_entry(
        self, 
        review_id: int, 
        competency_id: int, 
        answer: str, 
        score: int
    ) -> ReviewEntry:
        """Добавление записи в ревью."""
        self.logger.info(
            "review_entry_added",
            action="add_review_entry",
            review_id=review_id,
            competency_id=competency_id,
            score=score
        )
        
        # Валидация
        if not answer or len(answer.strip()) == 0:
            raise ValueError("Answer не может быть пустым")
        
        if not (1 <= score <= 5):
            raise ValueError("Score должен быть от 1 до 5")
        
        entry = ReviewEntry(
            id=1,  # В реальности будет из БД
            review_id=review_id,
            competency_id=competency_id,
            answer=answer.strip(),
            score=score,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return entry
    
    def submit_review(self, review_id: int) -> Review:
        """Отправка ревью."""
        self.logger.info(
            "review_submitted",
            action="submit_review",
            review_id=review_id
        )
        
        # Заглушка - в реальности обновление в БД
        review = Review(
            id=review_id,
            user_id=1,
            cycle_id=1,
            review_type=ReviewType.SELF,
            status=ReviewStatus.SUBMITTED,
            platform=Platform.WEB,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return review


class SummaryService:
    """Сервис для работы со сводками."""
    
    def __init__(self):
        self.logger = logger
    
    def generate_summary(
        self, 
        user_id: int, 
        cycle_id: int,
        review_data: Dict[str, Any]
    ) -> Summary:
        """Генерация сводки."""
        self.logger.info(
            "summary_generation_started",
            action="generate_summary",
            user_id=user_id,
            cycle_id=cycle_id
        )
        
        # Валидация данных
        if not review_data.get('self_reviews'):
            raise ValueError("Отсутствуют данные самооценки")
        
        # Анализ данных (заглушка)
        strengths = self._analyze_strengths(review_data)
        areas_for_growth = self._analyze_areas_for_growth(review_data)
        next_steps = self._generate_next_steps(review_data)
        
        summary = Summary(
            id=1,  # В реальности будет из БД
            user_id=user_id,
            cycle_id=cycle_id,
            strengths=strengths,
            areas_for_growth=areas_for_growth,
            next_steps=next_steps,
            generated_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.logger.info(
            "summary_generated",
            action="generate_summary",
            summary_id=summary.id,
            user_id=user_id
        )
        
        return summary
    
    def _analyze_strengths(self, review_data: Dict[str, Any]) -> List[str]:
        """Анализ сильных сторон."""
        strengths = []
        for review in review_data.get('self_reviews', []):
            if review.get('score', 0) >= 4:
                strengths.append(f"Высокая оценка в {review.get('competency', 'компетенции')}")
        return strengths[:3]  # Топ-3
    
    def _analyze_areas_for_growth(self, review_data: Dict[str, Any]) -> List[str]:
        """Анализ зон роста."""
        areas = []
        for review in review_data.get('self_reviews', []):
            if review.get('score', 0) <= 2:
                areas.append(f"Развитие в {review.get('competency', 'компетенции')}")
        return areas[:3]  # Топ-3
    
    def _generate_next_steps(self, review_data: Dict[str, Any]) -> List[str]:
        """Генерация следующих шагов."""
        return [
            "Продолжить работу над текущими проектами",
            "Изучить новые инструменты тестирования",
            "Участвовать в code review коллег"
        ]


class TemplateService:
    """Сервис для работы с шаблонами."""
    
    def __init__(self):
        self.logger = logger
    
    def create_template(
        self, 
        competency_id: int, 
        title: str, 
        content: str
    ) -> Template:
        """Создание шаблона."""
        self.logger.info(
            "template_creation_started",
            action="create_template",
            competency_id=competency_id,
            title=title
        )
        
        # Валидация
        if not title or len(title.strip()) == 0:
            raise ValueError("Title не может быть пустым")
        
        if not content or len(content.strip()) == 0:
            raise ValueError("Content не может быть пустым")
        
        template = Template(
            id=1,  # В реальности будет из БД
            competency_id=competency_id,
            title=title.strip(),
            content=content.strip(),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.logger.info(
            "template_created",
            action="create_template",
            template_id=template.id,
            competency_id=competency_id
        )
        
        return template
    
    def get_templates_by_competency(self, competency_id: int) -> List[Template]:
        """Получение шаблонов по компетенции."""
        self.logger.info(
            "templates_lookup",
            action="get_templates_by_competency",
            competency_id=competency_id
        )
        
        # Заглушка - в реальности запрос к БД
        return [
            Template(
                id=1,
                competency_id=competency_id,
                title="Базовый шаблон",
                content="Опишите ваш опыт в данной компетенции...",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]


# Глобальные экземпляры сервисов для тестирования
user_service = UserService()
review_service = ReviewService()
competency_service = CompetencyService()
template_service = TemplateService()
