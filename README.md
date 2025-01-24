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


## Optional, populate the database with sample data

- Download the Nexus data (only metadata) from:
```
https://openbraininstitute-my.sharepoint.com/:u:/g/personal/jean-denis_courcol_openbraininstitute_org/EVY7UqF-iHtFs1SmpWoykC4B5vdckmGWlM9OQTe8aTTqIA?e=dHJ9Os
```
- Untar in a directory called `out`
```
tar xzf out.tar.gz
```
- Import data into the specified database:
```
DB_HOST=127.0.0.1 DB_PORT=5433 uv run -m app.cli.import-data --input_dir ./out
```

## Legacy notes, to be cleaned up

```
# setup postgres to use full text search (VectorTS)

# test_legacy / test_dump can be used to test legacy calls
# test_dump is going through all the nexus rest calls in nexus_use_case_dump and executes these calls
```
