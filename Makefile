SHELL := /bin/bash

export ENVIRONMENT ?= dev
export APP_NAME := entitycore
export APP_VERSION := $(shell git describe --abbrev --dirty --always --tags)
export COMMIT_SHA := $(shell git rev-parse HEAD)
export IMAGE_NAME ?= $(APP_NAME)
export IMAGE_TAG ?= $(APP_VERSION)-$(ENVIRONMENT)

.PHONY: help install compile-deps upgrade-deps check-deps format lint build publish test-local test-docker run-local run-docker destroy migration

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-23s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies into .venv
	uv sync --no-install-project

compile-deps:  ## Create or update the lock file, without upgrading the version of the dependencies
	uv lock

upgrade-deps:  ## Create or update the lock file, using the latest version of the dependencies
	uv lock --upgrade

check-deps:  ## Check that the dependencies in the existing lock file are valid
	uv lock --locked

format:  ## Run formatters
	uv run -m ruff format
	uv run -m ruff check --fix

lint:  ## Run linters
	uv run -m ruff format --check
	uv run -m ruff check
	uv run -m mypy app

build:  ## Build the Docker image
	docker compose --progress=plain build app

publish: build  ## Publish the Docker image to DockerHub
	docker compose push app

test-local: export DB_HOST=127.0.0.1
test-local: export DB_PORT=5434
test-local: export DB_USER=test
test-local: export DB_PASS=test
test-local: export DB_NAME=test
test-local:  ## Run tests locally
	docker compose up --wait db-test
	uv run -m alembic upgrade head
	uv run -m pytest -sv tests
	uv run -m coverage xml
	uv run -m coverage html

test-docker: build  ## Run tests in Docker
	docker compose run --rm --remove-orphans test

run-local: export UVICORN_HOST=127.0.0.1
run-local: export UVICORN_PORT=8000
run-local: export UVICORN_RELOAD=true
run-local: export DB_HOST=127.0.0.1
run-local: export DB_PORT=5433
run-local: build  ## Run the application locally
	docker compose up --wait db
	uv run -m alembic upgrade head
	uv run uvicorn app:app

run-docker: build  ## Run the application in Docker
	docker compose up app --watch --remove-orphans

destroy: export COMPOSE_PROFILES=run,test
destroy:  ## Take down the application and remove the volumes
	docker compose down --remove-orphans --volumes

migration: export DB_HOST=127.0.0.1
migration: export DB_PORT=5433
migration:  ## Create or update the alembic migration
	docker compose up --wait db
	uv run -m alembic upgrade head
	uv run -m alembic revision --autogenerate
