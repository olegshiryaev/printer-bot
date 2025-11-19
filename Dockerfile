FROM python:3.12-slim

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем только метаданные
COPY pyproject.toml poetry.lock ./

# Устанавливаем poetry + зависимости БЕЗ установки самого проекта
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi

# Копируем код
COPY . .

# Явно ставим psycopg2-binary (на всякий случай, даже если используем asyncpg)
RUN pip install --no-cache-dir psycopg2-binary

EXPOSE 8000

CMD ["python", "run.py"]