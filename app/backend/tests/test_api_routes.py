"""Тесты для API маршрутов."""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from app.backend.src.main import create_app
from app.backend.src.domain.models import UserRole, Platform


class TestAPIHealth:
    """Тесты для health check."""
    
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    def test_healthcheck_success(self):
        """Тест успешного health check."""
        response = self.client.get("/healthz")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "qa-assessment-api"
    
    def test_metrics_endpoint(self):
        """Тест endpoint метрик."""
        response = self.client.get("/metrics")
        
        assert response.status_code == 200
        assert "http_requests_total" in response.text
        assert "llm_requests_total" in response.text


class TestReviewAPI:
    """Тесты для API ревью."""
    
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    @patch('app.backend.src.api.routes.user_service')
    def test_start_self_review_success(self, mock_user_service):
        """Тест успешного начала самооценки."""
        # Настройка мока
        mock_user = Mock()
        mock_user.id = 1
        mock_user.role = UserRole.USER
        mock_user_service.get_user_by_handle.return_value = mock_user
        
        with patch('app.backend.src.api.routes.review_service') as mock_review_service:
            mock_review = Mock()
            mock_review.id = 1
            mock_review.user_id = 1
            mock_review_service.start_review.return_value = mock_review
            
            response = self.client.post(
                "/api/reviews/self/start",
                headers={"X-User-Id": "1", "X-User-Role": "user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["review_id"] == 1
            assert data["user_id"] == 1
    
    @patch('app.backend.src.api.routes.user_service')
    def test_start_peer_review_success(self, mock_user_service):
        """Тест успешного начала взаимной оценки."""
        # Настройка мока
        mock_user = Mock()
        mock_user.id = 2
        mock_user.role = UserRole.USER
        mock_user_service.get_user_by_handle.return_value = mock_user
        
        with patch('app.backend.src.api.routes.review_service') as mock_review_service:
            mock_review = Mock()
            mock_review.id = 2
            mock_review.user_id = 2
            mock_review_service.start_review.return_value = mock_review
            
            response = self.client.post(
                "/api/reviews/peer/start",
                json={"target_user_handle": "peer_user"},
                headers={"X-User-Id": "1", "X-User-Role": "user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["review_id"] == 2
            assert data["target_user_id"] == 2
    
    def test_start_review_unauthorized(self):
        """Тест начала ревью без авторизации."""
        response = self.client.post("/api/reviews/self/start")
        
        assert response.status_code == 401
    
    @patch('app.backend.src.api.routes.review_service')
    def test_add_review_entry_success(self, mock_review_service):
        """Тест успешного добавления записи в ревью."""
        mock_entry = Mock()
        mock_entry.id = 1
        mock_entry.review_id = 1
        mock_entry.competency_id = 1
        mock_entry.answer = "Test answer"
        mock_entry.score = 4
        mock_review_service.add_review_entry.return_value = mock_entry
        
        response = self.client.post(
            "/api/reviews/1/entry",
            json={
                "competency_id": 1,
                "answer": "Test answer",
                "score": 4
            },
            headers={"X-User-Id": "1", "X-User-Role": "user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["entry_id"] == 1
        assert data["answer"] == "Test answer"
        assert data["score"] == 4
    
    def test_add_review_entry_invalid_score(self):
        """Тест добавления записи с некорректным score."""
        response = self.client.post(
            "/api/reviews/1/entry",
            json={
                "competency_id": 1,
                "answer": "Test answer",
                "score": 6  # Некорректный score
            },
            headers={"X-User-Id": "1", "X-User-Role": "user"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.backend.src.api.routes.llm_client')
    def test_refine_review_entry_success(self, mock_llm_client):
        """Тест успешного рефакторинга записи ревью."""
        mock_response = Mock()
        mock_response.refined = "Улучшенный текст"
        mock_response.improvement_hints = ["Подсказка 1", "Подсказка 2"]
        mock_llm_client.refine_text.return_value = mock_response
        
        response = self.client.post(
            "/api/reviews/1/refine",
            json={"entry_id": 1},
            headers={"X-User-Id": "1", "X-User-Role": "user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["refined"] == "Улучшенный текст"
        assert len(data["improvement_hints"]) == 2
    
    @patch('app.backend.src.api.routes.llm_client')
    def test_detect_conflicts_success(self, mock_llm_client):
        """Тест успешного обнаружения конфликтов."""
        mock_response = Mock()
        mock_response.duplicates = [
            Mock(self_item="Item 1", peer_item="Item 2", similarity=0.8)
        ]
        mock_response.contradictions = [
            Mock(self_item="Score 5", peer_item="Score 2", competency="test")
        ]
        mock_llm_client.detect_conflicts.return_value = mock_response
        
        response = self.client.post(
            "/api/reviews/1/detect_conflicts",
            headers={"X-User-Id": "1", "X-User-Role": "user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["duplicates"]) == 1
        assert len(data["contradictions"]) == 1


class TestSummaryAPI:
    """Тесты для API сводок."""
    
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    @patch('app.backend.src.api.routes.task_manager')
    def test_generate_summary_success(self, mock_task_manager):
        """Тест успешной генерации сводки."""
        mock_task_manager.start_summary_generation.return_value = "task-123"
        
        response = self.client.post(
            "/api/summaries/1/generate?cycle_id=1",
            headers={"X-User-Id": "1", "X-User-Role": "user"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "task-123"
        assert data["status"] == "started"
    
    @patch('app.backend.src.api.routes.task_manager')
    def test_get_summary_status(self, mock_task_manager):
        """Тест получения статуса сводки."""
        mock_task_manager.get_task_status.return_value = {
            "task_id": "task-123",
            "status": "completed",
            "result": {"summary_id": 1}
        }
        
        response = self.client.get(
            "/api/tasks/task-123/status",
            headers={"X-User-Id": "1", "X-User-Role": "user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"]["summary_id"] == 1


class TestAdminAPI:
    """Тесты для админ API."""
    
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    @patch('app.backend.src.api.routes.competency_service')
    def test_create_competency_admin_success(self, mock_competency_service):
        """Тест успешного создания компетенции админом."""
        mock_competency = Mock()
        mock_competency.id = 1
        mock_competency.key = "test_skill"
        mock_competency.title = "Test Skill"
        mock_competency_service.create_competency.return_value = mock_competency
        
        response = self.client.post(
            "/api/admin/competencies",
            json={
                "key": "test_skill",
                "title": "Test Skill",
                "description": "Test description"
            },
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["competency_id"] == 1
        assert data["key"] == "test_skill"
    
    def test_create_competency_user_forbidden(self):
        """Тест создания компетенции обычным пользователем."""
        response = self.client.post(
            "/api/admin/competencies",
            json={
                "key": "test_skill",
                "title": "Test Skill"
            },
            headers={"X-User-Id": "1", "X-User-Role": "user"}
        )
        
        assert response.status_code == 403
    
    @patch('app.backend.src.api.routes.competency_service')
    def test_get_competencies_success(self, mock_competency_service):
        """Тест получения списка компетенций."""
        mock_competencies = [
            Mock(id=1, key="skill1", title="Skill 1", is_active=True),
            Mock(id=2, key="skill2", title="Skill 2", is_active=True)
        ]
        mock_competency_service.get_active_competencies.return_value = mock_competencies
        
        response = self.client.get(
            "/api/admin/competencies",
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["competencies"]) == 2
        assert data["competencies"][0]["key"] == "skill1"
    
    @patch('app.backend.src.api.routes.template_service')
    def test_create_template_success(self, mock_template_service):
        """Тест успешного создания шаблона."""
        mock_template = Mock()
        mock_template.id = 1
        mock_template.competency_id = 1
        mock_template.title = "Test Template"
        mock_template_service.create_template.return_value = mock_template
        
        response = self.client.post(
            "/api/admin/templates",
            json={
                "competency_id": 1,
                "title": "Test Template",
                "content": "Test content"
            },
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["template_id"] == 1
        assert data["title"] == "Test Template"
    
    def test_create_template_invalid_data(self):
        """Тест создания шаблона с некорректными данными."""
        response = self.client.post(
            "/api/admin/templates",
            json={
                "competency_id": 1,
                "title": "",  # Пустой title
                "content": "Test content"
            },
            headers={"X-User-Id": "1", "X-User-Role": "admin"}
        )
        
        assert response.status_code == 422


class TestBotAPI:
    """Тесты для бот API."""
    
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    def test_slack_webhook_success(self):
        """Тест успешного Slack webhook."""
        response = self.client.post(
            "/bot/slack/events",
            json={"type": "url_verification", "challenge": "test_challenge"}
        )
        
        # Должен вернуть 200 даже без токенов (заглушка)
        assert response.status_code == 200
    
    def test_telegram_webhook_success(self):
        """Тест успешного Telegram webhook."""
        response = self.client.post(
            "/bot/telegram/webhook",
            json={"update_id": 1, "message": {"text": "/start"}}
        )
        
        # Должен вернуть 200 даже без токена (заглушка)
        assert response.status_code == 200


class TestAPIValidation:
    """Тесты валидации API."""
    
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    def test_invalid_json_request(self):
        """Тест запроса с некорректным JSON."""
        response = self.client.post(
            "/api/reviews/self/start",
            data="invalid json",
            headers={"Content-Type": "application/json", "X-User-Id": "1"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """Тест запроса с отсутствующими обязательными полями."""
        response = self.client.post(
            "/api/reviews/1/entry",
            json={"competency_id": 1},  # Отсутствует answer и score
            headers={"X-User-Id": "1", "X-User-Role": "user"}
        )
        
        assert response.status_code == 422
    
    def test_invalid_user_id_format(self):
        """Тест с некорректным форматом user_id."""
        response = self.client.post(
            "/api/reviews/self/start",
            headers={"X-User-Id": "invalid", "X-User-Role": "user"}
        )
        
        assert response.status_code == 422


class TestAPIMetrics:
    """Тесты метрик API."""
    
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    def test_metrics_collection(self):
        """Тест сбора метрик при запросах."""
        # Делаем несколько запросов
        self.client.get("/healthz")
        self.client.get("/metrics")
        self.client.get("/healthz")
        
        # Проверяем метрики
        response = self.client.get("/metrics")
        assert response.status_code == 200
        
        metrics_text = response.text
        assert "http_requests_total" in metrics_text
        assert "http_request_duration_seconds" in metrics_text
    
    def test_metrics_format(self):
        """Тест формата метрик Prometheus."""
        response = self.client.get("/metrics")
        assert response.status_code == 200
        
        metrics_text = response.text
        
        # Проверяем формат Prometheus
        assert "# HELP" in metrics_text
        assert "# TYPE" in metrics_text
        assert "counter" in metrics_text
        assert "histogram" in metrics_text
