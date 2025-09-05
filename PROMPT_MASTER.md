Роль и стиль
Ты — опытный Solution Architect и Senior Full-Stack/ML Engineer. Пиши код Production-качества, минимально лишний, со строгой типизацией, комментариями и тестами. Не задавай вопросов — делай разумные допущения и явно фиксируй их в README. Отдавай результат итерациями: сначала структура репо, затем ключевые модули, затем интеграции.
Цель
Сгенерировать полный работающий проект бота для самооценки и взаимной оценки сотрудников (QA-команда), со следующими возможностями:
	•	Типы оценивания: Self-assessment и Peer-review.
	•	Шаблоны ответов по компетенциям.
	•	Анализ/рефакторинг текста (ясность, дубликаты, несоответствия), подсказки по улучшению.
	•	Сводка (summary) по сотруднику.
	•	Интеграции: Slack и Telegram (slash-команды).
	•	Веб-интерфейс администратора (минимальный) для управления компетенциями, шаблонами, волнами оценок, ролями.
	•	Аудит-логи всех взаимодействий.
	•	Latency бюджет ответа бота ≤ 5 секунд (используй стриминг, кэширование, асинхронщину).
	•	Бэкенд на Python, фронтенд на React.
Технологический стек (фиксированный)
	•	Backend: Python 3.11+, FastAPI, uvicorn, async SQLAlchemy, Pydantic, httpx, Celery (фоновые задачи), Redis (кэш/очереди), PostgreSQL.
	•	LLM: OpenAI GPT-4o/GPT-4.1 (через официальный SDK), фолбэк на gpt-3.5 для дешёвых задач; embeddings для поиска шаблонов/подсказок.
	•	Front-end (Admin): React + Vite, TypeScript, shadcn/ui, Zustand, React Query.
	•	Bots: Slack Bolt for Python, python-telegram-bot.
	•	Infra: Docker + docker-compose, Makefile, Alembic (миграции), pre-commit hooks, Ruff + Black, pytest.
	•	Observability: структурные логи (JSON), запрос/ответ LLM с трейс-ID, Prometheus метрики (FastAPI instrument), Sentry.
	•	Security: OAuth for Admin (e.g., GitHub OAuth), HMAC подпись вебхуков, RBAC, секреты через env.
Функциональные требования
Slash-команды
	•	/self_review — запустить самооценку (DM диалог).
	•	/peer_review @username — начать отзыв о коллеге.
	•	/summary @username — показать сводку по сотруднику.
Компетенции (редактируемые из админки)
	•	Аналитическое мышление
	•	Качество баг-репортов
	•	Работа с тестовой документацией
	•	Взаимодействие с разработчиками
	•	Самостоятельность / инициативность
LLM-функции
	1	Генерация шаблонов ответов по компетенциям (тон: профессиональный, конкретика, примеры).
	2	Рефакторинг текста: упрощение формулировок, устранение двусмысленностей, улучшение структуры.
	3	Дедупликация и подсветка несоответствий (пример: самооценка vs peer-фидбек).
	4	Сводка: краткая, action-oriented; выделить сильные стороны, зоны роста, конкретные рекомендации.
	5	Следующие шаги: авто-подсказки «что улучшить за 2 недели/квартал» (SMART).
Нефункциональные
	•	Ответ ≤ 5с:
	◦	Стриминг в чатах (где возможно), прерывание по таймауту, отдача краткой версии + последующая до-догрузка подробностей (edit сообщение).
	◦	Aggressive кэширование шаблонов/эмбеддингов.
	◦	Асинхронные фоновые сравнения/сводки (Celery) с уведомлением по готовности.
	•	Полный аудит: кто/когда/что ввёл, какие подсказки дал LLM, какие правки приняты.
	•	PII: маскирование имён в логах, хранение сырых текстов шифрованно (at rest).
	•	Мультиязык (RU/EN), локализация через i18n файлы.
Архитектура и артефакты (что сгенерировать)
	1	Monorepo:

/app
  /backend
    /src
      api/ (FastAPI routers)
      bots/ (slack, telegram adapters)
      core/ (config, logging, security)
      domain/ (models, services, use-cases)
      llm/ (clients, prompts, pipelines, embeddings)
      repos/ (SQLAlchemy repos)
      schemas/ (Pydantic)
      tasks/ (Celery tasks)
      utils/
    alembic/
    tests/
  /frontend-admin
    src/ (React TS)
    public/
  /infra
    docker-compose.yml
    Dockerfiles/
    Makefile
    prometheus.yml
    grafana/
README.md
	2	Data-model (PostgreSQL, миграции Alembic)
	◦	users(id, ext_platform, handle, email, role[admin|user], created_at)
	◦	competencies(id, key, title, description, is_active)
	◦	review_cycles(id, title, starts_at, ends_at, status)
	◦	reviews(id, cycle_id, author_id, subject_id, type[self|peer], status[draft|submitted], lang, created_at)
	◦	review_entries(id, review_id, competency_id, raw_text, refined_text, llm_score jsonb, hints jsonb)
	◦	conflicts(id, review_id, competency_id, kind[dup|contradiction], details jsonb)
	◦	summaries(id, subject_id, cycle_id, content, created_at)
	◦	audit_logs(id, user_id, action, payload jsonb, created_at)
	◦	templates(id, competency_id, language, content, version, embedding vector)
	3	REST/WS API (FastAPI)
	◦	POST /api/reviews/self/start
	◦	POST /api/reviews/peer/start
	◦	POST /api/reviews/{id}/entry (add/update)
	◦	POST /api/reviews/{id}/refine (LLM refactor)
	◦	POST /api/reviews/{id}/detect_conflicts
	◦	POST /api/summaries/{user_id}/generate?cycle_id=
	◦	Admin: CRUD для компетенций, шаблонов, циклов, ролей.
	◦	GET /api/audit (фильтры, пагинация).
	◦	Webhooks: /bot/slack/events, /bot/telegram/webhook.
	4	Slack/Telegram адаптеры
	◦	Регистрация slash-команд.
	◦	Диалоговые сцены/состояния (FSM) для пошагового сбора ответов.
	◦	Поток: старт → выбор цикла → по компетенциям вопросы → предпросмотр → рефакторинг → сабмит.
	◦	/summary @user рендерит краткий summary + кнопку «детали» (разворачивается/досылается).
	5	LLM-оркестрация
	◦	Клиент с ретраями, таймаутами, трейс-ID.
	◦	Промты (ниже) как JSONSchema-ориентированные; парсинг ответа строго по схеме.
	◦	Embeddings для поиска релевантных шаблонов (cosine sim, Top-k).
	◦	Guardrails: длина, тон, запрет PII в сводке, чек-листы перед финальным выводом.
	6	Frontend-admin (React)
	◦	Страницы: Login (OAuth), Competencies, Templates, Review Cycles, Users, Audit.
	◦	Формы валидации (Zod), таблицы (DataTable), фильтры, экспорты CSV.
	◦	Темизация, i18n (RU/EN), доступность (a11y).
	7	Тесты
	◦	unit (сервисы, llm-парсинг),
	◦	e2e (API + временная SQLite),
	◦	контрактные тесты интеграций Slack/Telegram (моки).
	8	Инфра
	◦	Dockerfiles, docker-compose (db, redis, api, worker, admin).
	◦	Prometheus + Grafana пример дашбордов (RPS, p95, токены, ошибки).
	◦	pre-commit, линтеры, форматтеры.
	◦	README с командами запуска, миграциями, переменными окружения.
Переменные окружения (пример)

OPENAI_API_KEY={{OPENAI_API_KEY}}
DB_DSN=postgresql+asyncpg://app:app@db:5432/app
REDIS_URL=redis://redis:6379/0
SENTRY_DSN={{SENTRY_DSN}}
SLACK_SIGNING_SECRET={{SLACK_SIGNING_SECRET}}
SLACK_BOT_TOKEN={{SLACK_BOT_TOKEN}}
TELEGRAM_BOT_TOKEN={{TELEGRAM_BOT_TOKEN}}
ADMIN_OAUTH_CLIENT_ID={{CLIENT_ID}}
ADMIN_OAUTH_CLIENT_SECRET={{CLIENT_SECRET}}
LLM-подпромты (вшить в код)
1) Генерация шаблона ответа по компетенции
System:«Ты — помогаешь сотруднику формулировать краткие, конкретные ответы по компетенциям QA. Тон: профессиональный, доброжелательный, без жаргона. Ограничение — до 120 слов. Возвращай JSON по схеме.»
JSON Schema (Pydantic модуль тоже сгенерируй):

{
  "type": "object",
  "properties": {
    "outline": {"type":"string"},
    "example": {"type":"string"},
    "bullet_points": {"type":"array","items":{"type":"string","maxLength":120}, "minItems":3, "maxItems":5}
  },
  "required": ["outline","example","bullet_points"]
}
User (пример):{"competency":"Качество баг-репортов","context":"Проект А, мобайл, релизы 2/мес, внедрил шаблон баг-репорта"}
2) Рефакторинг текста пользователя
System: «Перепиши текст короче и яснее, сохрани факты, убери воду, предложи улучшения. Верни JSON.»

{
  "type":"object",
  "properties":{
    "refined":"string",
    "improvement_hints":{"type":"array","items":{"type":"string"}, "minItems":2, "maxItems":6}
  },
  "required":["refined","improvement_hints"]
}
3) Поиск дубликатов и несоответствий
System: «Получаешь список пунктов self/peer. Найди дубликаты (похожие по смыслу) и противоречия (взаимоисключающие утверждения). Верни JSON.»

{
  "type":"object",
  "properties":{
    "duplicates":{"type":"array","items":{"type":"array","items":{"type":"integer"}}},
    "contradictions":{"type":"array","items":{"type":"object","properties":{
      "self_idx":{"type":"integer"},
      "peer_idx":{"type":"integer"},
      "reason":{"type":"string"}
    }, "required":["self_idx","peer_idx","reason"]}}
  },
  "required":["duplicates","contradictions"]
}
4) Сводка (summary)
System: «Сделай короткий, практичный summary сотрудника: 3 сильные стороны, 3 зоны роста, 3 конкретных шага (SMART, ≤ 90 дней). Без PII. Верни JSON.»

{
  "type":"object",
  "properties":{
    "strengths":{"type":"array","items":{"type":"string"},"minItems":3,"maxItems":3},
    "areas_for_growth":{"type":"array","items":{"type":"string"},"minItems":3,"maxItems":3},
    "next_steps":{"type":"array","items":{"type":"string"},"minItems":3,"maxItems":3}
  },
  "required":["strengths","areas_for_growth","next_steps"]
}
Алгоритмы производительности (≤5 c)
	•	Немедленный ответ: «Принято, начнём с компетенции N» + 1-2 подсказки из кэша.
	•	Параллелим LLM-вызовы по компетенциям (async gather).
	•	Суммаризации/сравнения — в Celery, результат пушим в чат по готовности.
	•	Embeddings и шаблоны держим в Redis с TTL + warm-up при старте.
	•	Ограничь макс. токены и топ-p/temperature для быстрых задач; для сводки — отдельный профиль (более «умный»).
Безопасность/аудит
	•	Логи в JSON с полями: trace_id, user_id, platform, action, latency_ms, tokens_in/out.
	•	Маскирование @username и email в логах.
	•	Шифрование сырых ответов AES-GCM (ключ из env).
	•	RBAC: admin может видеть всё; пользователи — только свои и адресованные им peer-оценки.
Что отдать в ответ (итерация 1 сразу!)
	1	Структура репозитория и все Dockerfile/docker-compose.yml.
	2	FastAPI скелет с основными роутами + pydantic-схемы.
	3	Slack/Telegram вебхуки и обработчики /self_review, /peer_review, /summary.
	4	LLM-клиент, промты и строгий парсинг JSON.
	5	Миграции Alembic для всех таблиц.
	6	React-админка с CRUD по компетенциям/шаблонам/циклам.
	7	README с командами запуска:
	◦	make up, make migrate, make seed, make test
	◦	примеры .env
	8	10+ pytest-тестов (юнит/интеграция), моки LLM.
Acceptance Criteria (DoD)
	•	docker compose up поднимает API, Admin, DB, Redis, Worker.
	•	Slash-команды работают (моки), сохраняют черновики/результаты в БД.
	•	Админка позволяет создать цикл, компетенции, шаблоны.
	•	LLM-рефакторинг возвращает валидный JSON по схеме.
	•	Summary генерится (хоть и упрощённо) и доступен по /summary.
	•	Логи содержат trace_id и latency, p95 < 5с на демо-запросах.
Плейсхолдеры
Организация: Waxbill 
Брендинг/название бота: InsightQA 
Домены и URL вебхуков: http://localhost:8080 
Админ логин: Bulgakov@llcglobaladvisors.com
Сгенерируй весь код в нескольких последовательных блоках, начиная с структуры репозитория и README, затем backend, затем админку. В каждом блоке — только файлы, относящиеся к этому шагу.
