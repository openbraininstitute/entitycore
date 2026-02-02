# entitycore

## Requirements

- `uv`: https://docs.astral.sh/uv/getting-started/installation/
- `docker` and `docker compose`: https://docs.docker.com/compose/install/
- `postgresql` for building `psycopg2`:
  - `brew install postgresql` on Mac
  - `apt-get install gcc libc6-dev libpq-dev` on Linux (Ubuntu or Debian)

## Setup the virtualenv

```
$ make install
```

## Run the service in Docker

This will execute everything in Docker, without requiring authentication.

This will bring up a *persistent* database.
The service is automatically reloaded whenever the source code changes.

```
$ make run-docker  # or make run-local to run the service outside Docker
```

If everything worked correctly, you can access the openapi docs at http://127.0.0.1:8000

Note that the following ports are required by entitycore, so they shouldn't be already allocated by other services:

- `127.0.0.1:8000` for entitycore
- `127.0.0.1:9000-9001` for minio
- `127.0.0.1:5433` for postgresql

## Run tests in Docker

This will bring up a *non-persistent* database and run tests in Docker:

```
$ make test-docker  # or make test-local to run the tests outside Docker
```


## Cleaning up

In case of issues with the database, you can delete all the related Docker containers and volumes by running:

```
$ make destroy
```

## Optional, dump and restore the database

To dump and restore the database, you can optionally specify DUMPFILE when using:

```
$ make dump DUMPFILE=./data/db_2026.1.9.dump
```

```
$ make restore DUMPFILE=./data/db_2026.1.9.dump
```


## Available make targets

```
$ make
help                    Show this help
install                 Install dependencies into .venv
compile-deps            Create or update the lock file, without upgrading the version of the dependencies
upgrade-deps            Create or update the lock file, using the latest version of the dependencies
check-deps              Check that the dependencies in the existing lock file are valid
format                  Run formatters
lint                    Run linters
pip-audit               Run package auditing
build                   Build the Docker image
publish                 Publish the Docker image to DockerHub
test-local              Run tests locally
test-docker             Run tests in Docker
run-local               Run the application locally
run-docker              Run the application in Docker
destroy                 Take down the application and remove the volumes
migration               Create or update the alembic migration
dump                    Dump the local database to file
restore                 Delete and restore the local database from file
extract-traces          Extract response payloads generated in unit tests
update-asset-labels     Update asset-labels.md
```


Copyright © 2025-2026 Open Brain Institute
