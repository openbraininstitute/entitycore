SHELL := /bin/bash

export ENVIRONMENT ?= dev
export APP_NAME := entitycore
export APP_VERSION := $(shell git describe --abbrev --dirty --always --tags)
export COMMIT_SHA := $(shell git rev-parse HEAD)
export IMAGE_NAME ?= $(APP_NAME)
export IMAGE_TAG := $(APP_VERSION)
export IMAGE_TAG_ALIAS := latest
ifneq ($(ENVIRONMENT), prod)
	export IMAGE_TAG := $(IMAGE_TAG)-$(ENVIRONMENT)
	export IMAGE_TAG_ALIAS := $(IMAGE_TAG_ALIAS)-$(ENVIRONMENT)
endif

.PHONY: help install compile-deps upgrade-deps check-deps format lint build publish test-local test-docker run-local run-docker destroy migration

define load_env
	# all the variables in the included file must be prefixed with export
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
	uv run -m ruff format
	uv run -m ruff check --fix

lint:  ## Run linters
	uv run -m ruff format --check
	uv run -m ruff check
	uv run -m pyright app

build:  ## Build the Docker image
	docker compose --progress=plain build app

import:  ## Run the import on a database, assumes mba_hierarchy.json and out are in the current dir
	@$(call load_env,run-local)
	@test -n "$(PROJECT_ID_IMPORT)" || (echo "Please set the variable PROJECT_ID_IMPORT"; exit 1)
	@test -n "$(VIRTUAL_LAB_ID_IMPORT)" || (echo "Please set the variable VIRTUAL_LAB_ID_IMPORT"; exit 1)
	docker compose up --wait db
	uv run -m alembic upgrade head
	uv run -m app.cli.import_data --seed 0 hierarchy mba_hierarchy.json
	uv run -m app.cli.import_data --seed 1 run ./out --virtual-lab-id $(VIRTUAL_LAB_ID_IMPORT) --project-id $(PROJECT_ID_IMPORT)

organize-files:  ## Organize files locally by creating symlinks from the backup to the expected location
	@$(call load_env,run-local)
	docker compose up --wait db
	uv run -m app.cli.import_data organize-files $(if $(wildcard curated_files.txt),curated_files.txt,files.txt)

curate-files:
	@$(call load_env,run-local)
	docker compose up --wait db
	uv run -m app.cli.import_data curate-files files.txt curated_files.txt --out-dir ./curated

publish: build  ## Publish the Docker image to DockerHub
	docker compose push app

test-local:  ## Run tests locally
	@$(call load_env,test-local)
	docker compose up --wait db-test
	uv run -m alembic upgrade head
	uv run -m pytest
	uv run -m coverage xml
	uv run -m coverage html

test-docker: build  ## Run tests in Docker
	docker compose run --rm --remove-orphans test

run-local: ## Run the application locally
	@$(call load_env,run-local)
	docker compose up --wait db minio
	uv run -m alembic upgrade head
	uv run -m app run --host $(UVICORN_HOST) --port $(UVICORN_PORT) --reload

run-docker: build  ## Run the application in Docker
	docker compose up app --watch --remove-orphans

destroy: export COMPOSE_PROFILES=run,test
destroy:  ## Take down the application and remove the volumes
	docker compose down --remove-orphans --volumes

migration: MESSAGE ?= Default migration message
migration:  ## Create or update the alembic migration
	@$(call load_env,run-local)
	docker compose up --wait db
	uv run -m alembic upgrade head
	uv run -m alembic revision --autogenerate -m "$(MESSAGE)"

dump:  # Dump the local database to file
	docker compose up --wait db
	docker compose exec \
		-e DUMPFILE=$${DUMPFILE:-/data/db_$$APP_VERSION.dump} \
		-e PGUSER=$${PGUSER:-entitycore} -e PGPASSWORD=$${PGPASSWORD:-entitycore} \
		-e PGHOST=$${PGHOST:-db} -e PGPORT=$${PGPORT:-5432} -e PGDATABASE=$${PGDATABASE:-entitycore} \
		db bash -c '\
		echo "Dumping database $$PGDATABASE from $$PGHOST:$$PGPORT to $$DUMPFILE" && \
		pg_dump --dbname $$PGDATABASE -Fc -f $$DUMPFILE'

restore:  # Delete and restore the local database from file
	docker compose up --wait db
	docker compose exec \
		-e DUMPFILE=$${DUMPFILE:-/data/db_$$APP_VERSION.dump} \
		-e PGUSER=$${PGUSER:-entitycore} -e PGPASSWORD=$${PGPASSWORD:-entitycore} \
		-e PGHOST=$${PGHOST:-db} -e PGPORT=$${PGPORT:-5432} -e PGDATABASE=$${PGDATABASE:-entitycore} \
		db bash -c '\
		echo "Restoring database $$PGDATABASE from $$DUMPFILE to $$PGHOST:$$PGPORT" && \
		dropdb --force $$PGDATABASE && createdb $$PGDATABASE && \
		pg_restore --clean --if-exists --exit-on-error --no-owner --dbname $$PGDATABASE $$DUMPFILE \
		&& psql -c "ANALYZE;"'
