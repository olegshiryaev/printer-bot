FROM python:3.12-slim

# Только нужные системные зависимости для asyncpg (psycopg2 НЕ ставим!)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем только зависимости
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости БЕЗ установки проекта и без psycopg2
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi

# Копируем код
COPY . .

EXPOSE 8000

CMD ["python", "run.py"]