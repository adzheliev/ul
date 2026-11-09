.PHONY: sync lint test format

sync:
	uv sync

lint:
	uv run ruff check etl ml dags tests
	uv run ruff format --check etl ml dags tests

format:
	uv run ruff format etl ml dags tests
	uv run ruff check --fix etl ml dags tests

test:
	uv run pytest
