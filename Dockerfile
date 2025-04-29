FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=false

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev

COPY app ./app

FROM base AS api
CMD ["poetry", "run", "fastapi", "run", "app/api/main.py"]

FROM base AS bot
CMD ["poetry", "run", "python3", "-m", "app.bot.main"]
