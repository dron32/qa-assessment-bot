FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

RUN mkdir -p app/backend
COPY ./src ./app/backend/src
COPY ./alembic ./app/backend/alembic
COPY ./alembic.ini ./app/backend/alembic.ini
COPY ./tests ./app/backend/tests

EXPOSE 8000

CMD ["python", "-c", "import uvicorn; uvicorn.run('app.backend.src.main:app', host='0.0.0.0', port=8000)"]



