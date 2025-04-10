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

## Optional, populate the database with sample data

- Download the hierarchy:

```
aws s3 cp --no-sign-request s3://openbluebrain/Model_Data/Brain_atlas/Mouse/resolution_25_um/version_1.1.0/Parcellation_ontology/mba_hierarchy.json . 
```

- Download the Nexus data (only metadata) from:
```
https://openbraininstitute-my.sharepoint.com/:u:/g/personal/jean-denis_courcol_openbraininstitute_org/EVY7UqF-iHtFs1SmpWoykC4B5vdckmGWlM9OQTe8aTTqIA?e=dHJ9Os
```
- Untar the downloaded file (`out.tar` or `out.tar.gz`) in a directory called `out`:

```
$ tar xzf out.tar.gz
```

- Import data into the specified database:

```
$ make import
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
build                   Build the Docker image
import                  Run the import on a database, assumes mba_hierarchy.json and out are in the current dir
organize-files          Organize files locally by creating symlinks from the backup to the expected location
publish                 Publish the Docker image to DockerHub
test-local              Run tests locally
test-docker             Run tests in Docker
run-local               Run the application locally
run-docker              Run the application in Docker
destroy                 Take down the application and remove the volumes
migration               Create or update the alembic migration
```

## Legacy notes, to be cleaned up

```
# setup postgres to use full text search (VectorTS)

# test_legacy / test_dump can be used to test legacy calls
# test_dump is going through all the nexus rest calls in nexus_use_case_dump and executes these calls
```


Copyright © 2025 Open Brain Institute
