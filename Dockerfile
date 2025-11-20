FROM python:3.11-slim

# Устанавливаем системные зависимости для asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi

# Копируем код
COPY . .

EXPOSE 8000

CMD ["python", "run.py"]