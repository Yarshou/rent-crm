MYDIR ?= .

PROJECT_NAME := rent-crm

DEPS_FILES := \
    pyproject.toml \
    poetry.lock

.PHONY: lint-format
lint-format:
	poetry run ruff format
	poetry run ruff check --fix
	poetry run isort .

.PHONY: run
run:
	docker compose --env-file envs/.env -f docker-compose.yml up --build -d

.PHONY: stop
stop:
	docker compose down

.PHONY: make_migration
msg ?=
rev ?=
make_migration:
	docker exec -i rent-crm-api-1 poetry run alembic revision --autogenerate --rev-id "$(rev)" -m "$(msg)"

.PHONY: migrate
migrate:
	docker exec -i rent-crm-api-1 poetry run alembic upgrade head
