# syntax=docker/dockerfile:1

FROM python:3.14-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements-docker.txt .

RUN --mount=type=bind,source=docker-wheels,target=/wheels,readonly \
    python -m pip install \
    --no-index \
    --find-links=/wheels \
    -r requirements-docker.txt

COPY app ./app
COPY ui ./ui

EXPOSE 8000 8501

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]