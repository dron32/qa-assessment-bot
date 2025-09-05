"""Тесты для доменных сервисов."""

import pytest
from datetime import datetime
from unittest.mock import patch, Mock

from app.backend.src.domain.services import (
    UserService, CompetencyService, ReviewService, 
    SummaryService, TemplateService
)
from app.backend.src.domain.models import (
    UserRole, ReviewType, ReviewStatus, Platform
)


class TestUserService:
    """Тесты для UserService."""
    
    def setup_method(self):
        self.service = UserService()
    
    def test_create_user_success(self):
        """Тест успешного создания пользователя."""
        user = self.service.create_user(
            handle="testuser",
            email="test@example.com",
            role=UserRole.USER,
            platform=Platform.WEB
        )
        
        assert user.handle == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.platform == Platform.WEB
        assert isinstance(user.created_at, datetime)
    
    def test_create_user_with_whitespace(self):
        """Тест создания пользователя с пробелами."""
        user = self.service.create_user(
            handle="  testuser  ",
            email="  TEST@EXAMPLE.COM  ",
            role=UserRole.ADMIN
        )
        
        assert user.handle == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.ADMIN
    
    def test_create_user_empty_handle(self):
        """Тест создания пользователя с пустым handle."""
        with pytest.raises(ValueError, match="Handle не может быть пустым"):
            self.service.create_user(
                handle="",
                email="test@example.com"
            )
    
    def test_create_user_invalid_email(self):
        """Тест создания пользователя с некорректным email."""
        with pytest.raises(ValueError, match="Некорректный email"):
            self.service.create_user(
                handle="testuser",
                email="invalid-email"
            )
    
    def test_get_user_by_handle_admin(self):
        """Тест получения админа по handle."""
        user = self.service.get_user_by_handle("admin")
        
        assert user is not None
        assert user.handle == "admin"
        assert user.role == UserRole.ADMIN
        assert user.email == "admin@example.com"
    
    def test_get_user_by_handle_not_found(self):
        """Тест получения несуществующего пользователя."""
        user = self.service.get_user_by_handle("nonexistent")
        
        assert user is None
    
    def test_is_admin_true(self):
        """Тест проверки админа - true."""
        user = self.service.create_user(
            handle="admin",
            email="admin@example.com",
            role=UserRole.ADMIN
        )
        
        assert self.service.is_admin(user) is True
    
    def test_is_admin_false(self):
        """Тест проверки админа - false."""
        user = self.service.create_user(
            handle="user",
            email="user@example.com",
            role=UserRole.USER
        )
        
        assert self.service.is_admin(user) is False


class TestCompetencyService:
    """Тесты для CompetencyService."""
    
    def setup_method(self):
        self.service = CompetencyService()
    
    def test_create_competency_success(self):
        """Тест успешного создания компетенции."""
        competency = self.service.create_competency(
            key="test_skill",
            title="Test Skill",
            description="Test description"
        )
        
        assert competency.key == "test_skill"
        assert competency.title == "Test Skill"
        assert competency.description == "Test description"
        assert competency.is_active is True
    
    def test_create_competency_with_whitespace(self):
        """Тест создания компетенции с пробелами."""
        competency = self.service.create_competency(
            key="  TEST_SKILL  ",
            title="  Test Skill  ",
            description="  Test description  "
        )
        
        assert competency.key == "test_skill"
        assert competency.title == "Test Skill"
        assert competency.description == "Test description"
    
    def test_create_competency_empty_key(self):
        """Тест создания компетенции с пустым key."""
        with pytest.raises(ValueError, match="Key не может быть пустым"):
            self.service.create_competency(
                key="",
                title="Test Skill"
            )
    
    def test_create_competency_empty_title(self):
        """Тест создания компетенции с пустым title."""
        with pytest.raises(ValueError, match="Title не может быть пустым"):
            self.service.create_competency(
                key="test_skill",
                title=""
            )
    
    def test_get_active_competencies(self):
        """Тест получения активных компетенций."""
        competencies = self.service.get_active_competencies()
        
        assert len(competencies) == 2
        assert all(c.is_active for c in competencies)
        assert competencies[0].key == "analytical_thinking"
        assert competencies[1].key == "bug_reports"


class TestReviewService:
    """Тесты для ReviewService."""
    
    def setup_method(self):
        self.service = ReviewService()
    
    def test_start_review_success(self):
        """Тест успешного начала ревью."""
        review = self.service.start_review(
            user_id=1,
            cycle_id=1,
            review_type=ReviewType.SELF,
            platform=Platform.SLACK
        )
        
        assert review.user_id == 1
        assert review.cycle_id == 1
        assert review.review_type == ReviewType.SELF
        assert review.status == ReviewStatus.DRAFT
        assert review.platform == Platform.SLACK
    
    def test_start_review_invalid_user_id(self):
        """Тест начала ревью с некорректным user_id."""
        with pytest.raises(ValueError, match="Некорректный user_id"):
            self.service.start_review(
                user_id=0,
                cycle_id=1,
                review_type=ReviewType.SELF
            )
    
    def test_start_review_invalid_cycle_id(self):
        """Тест начала ревью с некорректным cycle_id."""
        with pytest.raises(ValueError, match="Некорректный cycle_id"):
            self.service.start_review(
                user_id=1,
                cycle_id=0,
                review_type=ReviewType.SELF
            )
    
    def test_add_review_entry_success(self):
        """Тест успешного добавления записи в ревью."""
        entry = self.service.add_review_entry(
            review_id=1,
            competency_id=1,
            answer="Хорошо анализирую проблемы",
            score=4
        )
        
        assert entry.review_id == 1
        assert entry.competency_id == 1
        assert entry.answer == "Хорошо анализирую проблемы"
        assert entry.score == 4
    
    def test_add_review_entry_empty_answer(self):
        """Тест добавления записи с пустым ответом."""
        with pytest.raises(ValueError, match="Answer не может быть пустым"):
            self.service.add_review_entry(
                review_id=1,
                competency_id=1,
                answer="",
                score=4
            )
    
    def test_add_review_entry_invalid_score(self):
        """Тест добавления записи с некорректным score."""
        with pytest.raises(ValueError, match="Score должен быть от 1 до 5"):
            self.service.add_review_entry(
                review_id=1,
                competency_id=1,
                answer="Test answer",
                score=6
            )
    
    def test_submit_review_success(self):
        """Тест успешной отправки ревью."""
        review = self.service.submit_review(review_id=1)
        
        assert review.id == 1
        assert review.status == ReviewStatus.SUBMITTED


class TestSummaryService:
    """Тесты для SummaryService."""
    
    def setup_method(self):
        self.service = SummaryService()
    
    def test_generate_summary_success(self):
        """Тест успешной генерации сводки."""
        review_data = {
            'self_reviews': [
                {'competency': 'analytical_thinking', 'score': 5},
                {'competency': 'bug_reports', 'score': 2}
            ]
        }
        
        summary = self.service.generate_summary(
            user_id=1,
            cycle_id=1,
            review_data=review_data
        )
        
        assert summary.user_id == 1
        assert summary.cycle_id == 1
        assert len(summary.strengths) > 0
        assert len(summary.areas_for_growth) > 0
        assert len(summary.next_steps) > 0
        assert isinstance(summary.generated_at, datetime)
    
    def test_generate_summary_no_self_reviews(self):
        """Тест генерации сводки без данных самооценки."""
        review_data = {}
        
        with pytest.raises(ValueError, match="Отсутствуют данные самооценки"):
            self.service.generate_summary(
                user_id=1,
                cycle_id=1,
                review_data=review_data
            )
    
    def test_analyze_strengths(self):
        """Тест анализа сильных сторон."""
        review_data = {
            'self_reviews': [
                {'competency': 'skill1', 'score': 5},
                {'competency': 'skill2', 'score': 4},
                {'competency': 'skill3', 'score': 2}
            ]
        }
        
        strengths = self.service._analyze_strengths(review_data)
        
        assert len(strengths) == 2  # Только score >= 4
        assert any('skill1' in s for s in strengths)
        assert any('skill2' in s for s in strengths)
    
    def test_analyze_areas_for_growth(self):
        """Тест анализа зон роста."""
        review_data = {
            'self_reviews': [
                {'competency': 'skill1', 'score': 5},
                {'competency': 'skill2', 'score': 1},
                {'competency': 'skill3', 'score': 2}
            ]
        }
        
        areas = self.service._analyze_areas_for_growth(review_data)
        
        assert len(areas) == 2  # Только score <= 2
        assert any('skill2' in s for s in areas)
        assert any('skill3' in s for s in areas)


class TestTemplateService:
    """Тесты для TemplateService."""
    
    def setup_method(self):
        self.service = TemplateService()
    
    def test_create_template_success(self):
        """Тест успешного создания шаблона."""
        template = self.service.create_template(
            competency_id=1,
            title="Test Template",
            content="Test content"
        )
        
        assert template.competency_id == 1
        assert template.title == "Test Template"
        assert template.content == "Test content"
        assert template.is_active is True
    
    def test_create_template_with_whitespace(self):
        """Тест создания шаблона с пробелами."""
        template = self.service.create_template(
            competency_id=1,
            title="  Test Template  ",
            content="  Test content  "
        )
        
        assert template.title == "Test Template"
        assert template.content == "Test content"
    
    def test_create_template_empty_title(self):
        """Тест создания шаблона с пустым title."""
        with pytest.raises(ValueError, match="Title не может быть пустым"):
            self.service.create_template(
                competency_id=1,
                title="",
                content="Test content"
            )
    
    def test_create_template_empty_content(self):
        """Тест создания шаблона с пустым content."""
        with pytest.raises(ValueError, match="Content не может быть пустым"):
            self.service.create_template(
                competency_id=1,
                title="Test Template",
                content=""
            )
    
    def test_get_templates_by_competency(self):
        """Тест получения шаблонов по компетенции."""
        templates = self.service.get_templates_by_competency(competency_id=1)
        
        assert len(templates) == 1
        assert templates[0].competency_id == 1
        assert templates[0].title == "Базовый шаблон"
        assert templates[0].is_active is True
