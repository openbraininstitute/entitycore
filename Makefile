SHELL := /bin/bash

export ENVIRONMENT ?= dev
export APP_NAME := test-db
export APP_VERSION := $(shell git describe --abbrev --dirty --always --tags)
export COMMIT_SHA := $(shell git rev-parse HEAD)
export IMAGE_NAME ?= $(APP_NAME)
export IMAGE_TAG ?= $(APP_VERSION)-$(ENVIRONMENT)

format:
	uv run -m ruff format
	uv run -m ruff check --fix

lint:
	uv run -m ruff format --check
	uv run -m ruff check
	uv run -m mypy app

.PHONY: test
test:
	uv run -m pytest test

build:  ## Build the Docker image
	docker compose build app

test-docker: build  ## Run tests in Docker
	docker compose run --rm --remove-orphans test
