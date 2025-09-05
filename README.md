# QA Assessment Bot — Monorepo

Репозиторий для бота самооценки и взаимной оценки (QA):
- **Backend API и Celery worker** — `app/backend` (FastAPI, SQLAlchemy, Alembic)
- **Веб-админка** — `app/frontend-admin` (React + Vite + TypeScript + shadcn/ui)
- **Инфраструктура** — `infra` (Docker Compose)

## Быстрый старт с Docker

1. **Скопируйте переменные окружения:**
```bash
cp .env.example .env
```

2. **Поднимите все сервисы:**
```bash
make up
```

3. **Проверьте статус:**
```bash
make ps
```

4. **Логи:**
```bash
make logs
```

5. **Остановка и очистка:**
```bash
make down
```

## Доступы по умолчанию

- **API**: http://localhost:8000
- **Админка**: http://localhost:5173
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## Переменные окружения (.env)

```bash
# База данных
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=qa_assessment
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# API
API_PORT=8000
ADMIN_PORT=5173

# LLM (опционально)
OPENAI_API_KEY=your-key-here
LLM_FAST_MODEL=gpt-4o-mini
LLM_SUMMARY_MODEL=gpt-4o

# Боты (опционально)
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
TELEGRAM_BOT_TOKEN=...
```

## Команды Makefile

- `make up` — build + up -d для docker-compose
- `make down` — остановить и удалить контейнеры и тома
- `make logs` — логи всех сервисов
- `make ps` — статус контейнеров
- `make test` — запуск тестов backend
- `make api-run` — локальный запуск uvicorn
- `make migrate` — применить миграции Alembic
- `make pre-commit-install` — установка git-хуков pre-commit

## Локальная разработка

### Backend
```bash
cd app/backend
python -m venv .venv
source .venv/bin/activate  # или .venv\Scripts\activate на Windows
pip install -r requirements.txt
make api-run
```

### Frontend
```bash
cd app/frontend-admin
npm install
npm run dev
```

## Структура проекта

```
.
├── app/
│   ├── backend/                    # FastAPI backend
│   │   ├── src/
│   │   │   ├── api/               # REST роуты
│   │   │   ├── bots/              # Slack/Telegram боты
│   │   │   ├── core/              # Конфиг, логи, auth
│   │   │   ├── llm/               # OpenAI клиент, промпты
│   │   │   ├── repos/             # SQLAlchemy репозитории
│   │   │   └── schemas/           # Pydantic схемы
│   │   ├── alembic/               # Миграции БД
│   │   ├── tests/                 # Тесты
│   │   └── requirements.txt
│   └── frontend-admin/            # React админка
│       ├── src/
│       │   ├── components/        # UI компоненты
│       │   ├── pages/             # Страницы
│       │   ├── i18n/              # Локализация
│       │   └── lib/               # Утилиты
│       ├── package.json
│       └── Dockerfile
├── infra/
│   └── docker-compose.yml         # Все сервисы
├── .pre-commit-config.yaml        # Git хуки
├── .gitignore
├── Makefile                       # Утилитарные команды
└── README.md
```

## Функциональность

### Backend
- ✅ FastAPI с async SQLAlchemy
- ✅ Alembic миграции (9 таблиц)
- ✅ LLM интеграция (OpenAI GPT-4)
- ✅ Slack/Telegram боты с FSM
- ✅ RBAC и аудит-логи
- ✅ JSON логирование
- ✅ 15+ unit/e2e тестов

### Frontend Admin
- ✅ React + Vite + TypeScript
- ✅ shadcn/ui компоненты
- ✅ React Query для API
- ✅ i18n (RU/EN)
- ✅ CRUD формы с валидацией
- ✅ Страницы: Login, Competencies, Templates, Cycles, Users, Audit

### Боты
- ✅ Slack Bolt с командами `/self_review`, `/peer_review`, `/summary`
- ✅ Telegram bot с теми же командами
- ✅ FSM для пошагового сбора ответов
- ✅ Быстрые ответы ≤5с + фоновая обработка
- ✅ LLM рефакторинг и сводки

## Мониторинг и Observability

### Prometheus метрики
- **HTTP метрики**: запросы, latency, статус коды
- **LLM метрики**: токены, операции, ошибки
- **Celery метрики**: задачи, длительность, статусы
- **Бизнес метрики**: ревью, сводки, платформы

### Grafana дашборды
1. Откройте http://localhost:3000
2. Логин: `admin`, пароль: `admin`
3. Дашборд "QA Assessment Monitoring" показывает:
   - HTTP запросы и latency
   - LLM операции и токены
   - Celery задачи
   - Системные метрики

### JSON логи
Все логи в JSON формате с полями:
- `trace_id` - для трассировки запросов
- `user_id` - ID пользователя
- `platform` - платформа (slack/telegram/web)
- `action` - действие
- `latency_ms` - время выполнения
- `tokens_in/out` - токены LLM
- PII данные автоматически маскируются

### Sentry интеграция
- Автоматические алерты на ошибки
- Теги для LLM операций
- Контекст запросов
- Настройка через `SENTRY_DSN`

## Тестирование

### Запуск тестов
```bash
# Все тесты
make test

# Конкретный тест
docker compose -f infra/docker-compose.yml exec api pytest tests/test_observability.py -v

# Тесты с покрытием
docker compose -f infra/docker-compose.yml exec api pytest tests/ --cov=src --cov-report=html
```

### Покрытие тестами
- **Доменные сервисы**: 10+ тестов для бизнес-логики
- **LLM парсинг**: тесты с моками OpenAI API
- **API маршруты**: тесты CRUD операций и RBAC
- **Боты**: контрактные тесты для Slack/Telegram
- **Observability**: тесты логирования, метрик, шифрования

### Сиды (Seed Data)

#### Заполнение дефолтными данными
```bash
make seed
```

#### Что создается:
- **5 пользователей**: админы, QA инженеры, технический пользователь
- **10 компетенций**: аналитическое мышление, баг-репорты, автоматизация и др.
- **5 шаблонов**: готовые шаблоны ответов для компетенций
- **3 цикла ревью**: квартальные и годовая оценка

#### Технический админ
- **Handle**: `admin`
- **Email**: `admin@qa-assessment.com`
- **Роль**: `ADMIN`
- **Платформа**: `WEB`
- **Технический**: `true`

## CI/CD

### GitHub Actions
Автоматический pipeline включает:
- **Линтеры**: Black, isort, flake8, mypy для Python
- **ESLint, Prettier** для TypeScript
- **Тесты**: backend и frontend с покрытием
- **Сборка**: Docker образы для API и frontend
- **Безопасность**: Trivy vulnerability scanner
- **Деплой**: автоматический деплой в staging

### Workflow файлы
- `.github/workflows/ci.yml` - основной CI/CD pipeline

## Производительность и кэширование

### Система кэширования
- **Redis TTL кэш** для шаблонов (1 час), эмбеддингов (24 часа), LLM ответов (30 минут)
- **Подогрев кэша** при старте приложения
- **Автоматическая инвалидация** при обновлении данных
- **Статистика кэша** доступна по `/cache/stats`

### Профили LLM
- **Быстрый профиль** (`gpt-4o-mini`): короткие ответы, низкие лимиты токенов, таймаут 2с
- **Умный профиль** (`gpt-4o`): детальные сводки, высокие лимиты токенов, таймаут 10с
- **Сбалансированный профиль**: по умолчанию для большинства задач

### Фолбэк механизмы
- **Быстрый ответ**: если >3с, отдается краткая версия + фоновая задача для полного ответа
- **Кэшированный ответ**: при ошибках используется кэш
- **Шаблонный ответ**: последний резерв при недоступности LLM

### Бенчмарк производительности (P95)
```bash
# Запуск бенчмарка
make benchmark
```

**Результаты P95:**
- **Cache Set**: 0.16ms
- **Cache Get**: 0.15ms  
- **LLM Fast Profile**: 106.03ms
- **LLM Smart Profile**: 506.33ms
- **Fallback Quick**: 2114.77ms

### Оптимизации
- **Кэширование эмбеддингов** снижает нагрузку на OpenAI API
- **Профили LLM** позволяют выбирать скорость vs качество
- **Фолбэк механизмы** обеспечивают отзывчивость при проблемах
- **Подогрев кэша** ускоряет первые запросы

## Миграции БД

```bash
# Применить миграции
make migrate

# Создать новую миграцию
cd app/backend && alembic revision --autogenerate -m "description"
```


