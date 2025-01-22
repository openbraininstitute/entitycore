# Install

Make sure you have `uv`: https://docs.astral.sh/uv/getting-started/installation/

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

## Local testing

This requires docker compose to be installed: https://docs.docker.com/compose/install/

Then one should be able to:
```
$ make test-docker
```

## Running against local database

In one terminal, this will bring up a *non-persistent* database:
```
$ docker compose run -P --remove-orphans db-test
```

Initialize DB
```
$ DB_HOST=127.0.0.1 DB_PORT=5434 DB_USER=test DB_PASS=test DB_NAME=test uv run python -m app db init
```

Or run tests:
```
$ DB_HOST=127.0.0.1 DB_PORT=5434 DB_USER=test DB_PASS=test DB_NAME=test uv run python -m pytest -sv test/
```
