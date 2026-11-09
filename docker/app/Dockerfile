FROM python:3.11-slim-bookworm AS app

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /usr/local/bin/uv

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH=/app \
    DBT_PROFILES_DIR=/app/dbt \
    PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY etl ./etl
COPY ml ./ml
COPY dbt ./dbt
COPY sql ./sql
COPY dags ./dags

CMD ["python", "-m", "etl.cli", "run-all"]

FROM app AS airflow

RUN uv venv /opt/airflow-venv \
    && uv pip install --python /opt/airflow-venv/bin/python "apache-airflow[postgres]==2.10.5"
ENV PATH="/opt/airflow-venv/bin:${PATH}" \
    AIRFLOW_HOME=/opt/airflow
