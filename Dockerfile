FROM python:3.12-slim

# Устанавливаем системные зависимости для asyncpg + psycopg2-binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем только зависимости
COPY pyproject.toml poetry.lock ./

# Устанавливаем poetry и зависимости
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# Копируем код
COPY . .

# Явно ставим psycopg2-binary (это спасает Render)
RUN pip install --no-cache-dir psycopg2-binary

EXPOSE 8000

CMD ["python", "run.py"]