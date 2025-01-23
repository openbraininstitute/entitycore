# Test DB

## Requirements

- `uv`: https://docs.astral.sh/uv/getting-started/installation/
- `docker` and `docker compose`: https://docs.docker.com/compose/install/


## Setup the virtualenv

```
$ uv sync
```

## Run the server in Docker

This will bring up a *persistent* database and run tests in Docker.
The server is automatically reloaded whenever the source code changes.

```
make run-docker
```

## Alternatively, run the server locally from the source code

This will bring up a *persistent* database and run tests locally:
The server is automatically reloaded whenever the source code changes.

```
make run-local
```

## Run tests in Docker

This will bring up a *non-persistent* database and run tests in Docker:

```
$ make test-docker
```

## Alternatively, run tests locally from the source code

This will bring up a *non-persistent* database and run tests locally:

```
$ make test-local
```

## Available make targets

```
$ make
help                    Show this help
format                  Run formatters
lint                    Run linters
build                   Build the Docker image
test-local              Run tests locally
test-docker             Run tests in Docker
run-local               Run the application locally
run-docker              Run the application in Docker
kill                    Take down the application and remove the volumes
migration               Create or update the alembic migration
```

## Legacy instructions, needed to populate the database with sample data

```
# setup virtualenv:
$ uv sync

# setup postgres to use full text search (VectorTS)

# update config.py accordingly (this part is a bit messy)
# DATABASE_URI is supposed to be used for the unit tests in test
# LEGACY_DATABASE_URI is supposed to be used to test legacy calls (test_legacy / test_dump)

# fetch the nexus data to import current OBI data (only metadata)
https://openbraininstitute-my.sharepoint.com/:u:/g/personal/jean-denis_courcol_openbraininstitute_org/EVY7UqF-iHtFs1SmpWoykC4B5vdckmGWlM9OQTe8aTTqIA?e=dHJ9Os

# untar in a directory called "out"

# import data (test.db is used for the name of the sqlite file):
uv run -m app.cli.import-data --db test.db --input_dir ./out

# test_dump is going through all the nexus rest calls in nexus_use_case_dump and executes these calls

#run server in order to test the API
uv run uvicorn app:app --reload
```
