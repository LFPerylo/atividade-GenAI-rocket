.PHONY: install hooks lint format typecheck test check api ui chat index eval quota docker-build up down

install:
	uv sync

hooks:
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy

test:
	uv run pytest

check: lint typecheck test

api:
	uv run cinerocket serve --reload

ui:
	uv run cinerocket ui

chat:
	uv run cinerocket chat

index:
	uv run cinerocket index build

eval:
	uv run cinerocket eval run

quota:
	uv run cinerocket quota

docker-build:
	docker compose build

up:
	docker compose up --build -d api ui

down:
	docker compose down
