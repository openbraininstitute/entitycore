SHELL := /bin/bash

export ENVIRONMENT ?= dev
export APP_NAME := entitycore
export APP_VERSION := $(shell git describe --abbrev --dirty --always --tags)
export COMMIT_SHA := $(shell git rev-parse HEAD)
export IMAGE_NAME ?= $(APP_NAME)
export IMAGE_TAG ?= $(APP_VERSION)-$(ENVIRONMENT)

.PHONY: help install compile-deps upgrade-deps check-deps format lint build publish test-local test-docker run-local run-docker destroy migration

define load_env
	$(eval ENV_FILE := .env.$(1))
	@echo "Loading env from $(ENV_FILE)"
	$(eval include $(ENV_FILE))
endef

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
	uv run -m ruff format app tests
	uv run -m ruff check --fix app tests

lint:  ## Run linters
	uv run -m ruff format --check app tests
	uv run -m ruff check app tests
	uv run -m mypy app

build:  ## Build the Docker image
	docker compose --progress=plain build app

import:  ## Run the import on a database, assumes mba_hierarchy.json and out are in the current dir
	@$(call load_env,test-local)
	uv run -m alembic upgrade head
	uv run -m app.cli.import-data hierarchy mba_hierarchy.json
	uv run -m app.cli.import-data run ./out --project-id $(PROJECT_ID_IMPORT)

publish: build  ## Publish the Docker image to DockerHub
	docker compose push app

test-local:  ## Run tests locally
	@$(call load_env,test-local)
	docker compose up --wait db-test
	uv run -m alembic upgrade head
	uv run -m pytest -sv tests
	uv run -m coverage xml
	uv run -m coverage html

test-docker: build  ## Run tests in Docker
	docker compose run --rm --remove-orphans test

run-local: ## Run the application locally
	@$(call load_env,run-local)
	docker compose up --wait db
	uv run -m alembic upgrade head
	uv run -m app run --host $(UVICORN_HOST) --port $(UVICORN_PORT) --reload

run-docker: build  ## Run the application in Docker
	docker compose up app --watch --remove-orphans

destroy: export COMPOSE_PROFILES=run,test
destroy:  ## Take down the application and remove the volumes
	docker compose down --remove-orphans --volumes

migration:  ## Create or update the alembic migration
	@$(call load_env,run-local)
	docker compose up --wait db
	uv run -m alembic upgrade head
	uv run -m alembic revision --autogenerate
