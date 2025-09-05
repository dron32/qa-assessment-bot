COMPOSE_FILE=infra/docker-compose.yml

.PHONY: up down logs ps pre-commit-install

up:
	docker compose -f $(COMPOSE_FILE) up -d --build

down:
	docker compose -f $(COMPOSE_FILE) down -v

logs:
	docker compose -f $(COMPOSE_FILE) logs -f | cat

ps:
	docker compose -f $(COMPOSE_FILE) ps | cat

pre-commit-install:
	pre-commit install

# Backend helpers (локальный запуск)
.PHONY: api-run migrate

api-run:
	uvicorn app.backend.src.main:app --host 0.0.0.0 --port 8000 --reload

migrate:
	cd app/backend && alembic upgrade head

.PHONY: test seed benchmark
test:
	docker compose -f $(COMPOSE_FILE) exec api pytest -q

seed:
	@echo "🌱 Заполнение базы данных дефолтными данными..."
	docker compose -f $(COMPOSE_FILE) exec api python app/backend/src/seeds/seed_db.py

benchmark:
	@echo "⚡ Запуск бенчмарка производительности..."
	docker compose -f $(COMPOSE_FILE) exec api python app/backend/src/benchmarks/performance.py


