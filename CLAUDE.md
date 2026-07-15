<!-- AUTO-GENERATED from .amazonq/rules/*.md — do not edit directly, run: make sync-rules -->

# Entitycore Project Rules

## Overview

Entitycore is a FastAPI REST service backed by PostgreSQL + SQLAlchemy (sync), with S3 (boto3) for file storage.
It manages scientific entities (morphologies, models, simulations, recordings, etc.) with per-project authorization.

## Tech Stack

- Python 3.12, FastAPI, SQLAlchemy (sync, psycopg2), Alembic, Pydantic v2, Pydantic-Settings
- S3 via boto3 (mocked with moto in tests)
- Auth: JWT (Keycloak), mocked in tests
- Package manager: `uv`
- Linter/formatter: `ruff`
- Type checker: `pyright`

## Project Structure

```
app/                    # Application source
  config.py             # Settings (pydantic-settings, env-based)
  application.py        # FastAPI app instance and lifespan
  db/model.py           # All SQLAlchemy models (single file)
  db/types.py           # Enums (EntityType, StorageType, etc.)
  db/session.py         # DatabaseSessionManager
  db/auth.py            # Row-level authorization filters
  routers/              # One file per entity type (FastAPI routers)
  routers/common.py     # Shared router utilities
  schemas/              # Pydantic request/response schemas
  service/              # Business logic layer
  repository/           # DB query layer
  dependencies/         # FastAPI dependency injection
  filters/              # fastapi-filter definitions
tests/                  # Pytest test suite
  conftest.py           # Shared fixtures (clients, db, entities)
  utils.py              # Test helpers (assert_request, add_db, ClientProxy, etc.)
  test_<entity>.py      # One test file per entity type
alembic/                # Database migrations
```

## Commands

- `make install` — install deps into .venv
- `make test-docker` — run full test suite in Docker (preferred)
- `make test-local` — run tests locally (requires `docker compose up --wait db-test`)
- `make run-docker` — run service in Docker with hot-reload
- `make run-local` — run service locally
- `make format` — run ruff format + fix
- `make lint` — run ruff check + pyright
- `make migration MESSAGE="..."` — create Alembic migration
- `make destroy` — tear down Docker containers and volumes

To run a single test locally:
```bash
PYTEST_ADDOPTS="-k test_create_one" make test-local
```

## Testing Conventions

### Framework & Configuration
- pytest with `--import-mode=importlib`
- Coverage target: 90% (`fail_under = 90`)
- Tests use a real PostgreSQL database (not SQLite), truncated between tests via `_db_cleanup` fixture

### Test Structure
- Each entity type has its own `tests/test_<entity>.py`
- Common fixtures in `tests/conftest.py`, helpers in `tests/utils.py`
- Tests are integration tests: they hit the FastAPI app via `TestClient` (sync)

### Key Fixtures
- `client` — authenticated as `user_1` with `PROJECT_ID` (default for most tests)
- `clients` — `ClientProxies` namedtuple with all user variants (user_1, user_2, user_3, admin, maintainer_1, etc.)
- `db` — SQLAlchemy `Session` (auto-rolled-back + truncated after each test)
- `person_id` — creates a Person agent (required as `created_by_id` for most entities)
- Entity-specific fixtures: `species_id`, `brain_region_id`, `subject_id`, `license_id`, `morphology_id`, `emodel_id`, etc.

### Auth in Tests
- Auth is mocked via `_override_check_user_info` (autouse via `client_no_auth`)
- Tokens are simple strings: `TOKEN_ADMIN`, `TOKEN_USER_1`, `TOKEN_USER_2`, etc.
- Headers: `AUTH_HEADER_*` + `PROJECT_HEADERS` / `UNRELATED_PROJECT_HEADERS`
- `ClientProxy` wraps `TestClient` to inject default auth headers

### Writing a New Test
1. Use `assert_request(client.post, url="/route", json={...})` for requests (asserts status 200 by default)
2. Use `add_db(db, Model(...))` to insert rows directly
3. Use `check_authorization(route, client_user_1, client_user_2, client_no_project, json_data)` to test auth
4. Use `check_entity_read_many`, `check_entity_update_one`, `check_entity_delete_one` for standard CRUD checks
5. Fixtures chain: most entities need `person_id` → `species_id` → `subject_id` → `brain_region_id`

### Test Patterns
```python
ROUTE = "/my-entity"
ADMIN_ROUTE = "/admin/my-entity"

@pytest.fixture
def json_data(subject_id, brain_region_id):
    return {
        "name": "test-name",
        "brain_region_id": str(brain_region_id),
        "subject_id": str(subject_id),
        "authorized_public": False,
    }

def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    assert data["name"] == json_data["name"]

def test_authorization(clients, json_data):
    check_authorization(ROUTE, clients.user_1, clients.user_2, clients.no_project, json_data)

def test_read_many(clients, json_data):
    check_entity_read_many(route=ROUTE, admin_route=ADMIN_ROUTE, clients=clients, json_data=json_data)

def test_update_one(clients, json_data):
    check_entity_update_one(
        route=ROUTE, admin_route=ADMIN_ROUTE, clients=clients,
        json_data=json_data,
        patch_payload={"name": "updated-name"},
        optional_payload={"description": "optional-desc"},
    )

def test_delete_one(db, clients, json_data):
    check_entity_delete_one(
        db, clients, ROUTE, ADMIN_ROUTE, json_data,
        expected_counts_before={MyModel: 1},
        expected_counts_after={MyModel: 0},
    )
```

### S3 / Assets in Tests
- S3 is mocked with `moto` (`mock_aws`), session-scoped
- Buckets are created once per session via `_create_buckets` fixture
- Use `upload_entity_asset(client, entity_type, entity_id, files, label)` to attach files

## Code Conventions

### Adding a New Entity Type
1. Add SQLAlchemy model in `app/db/model.py`
2. Add `EntityType` enum value in `app/db/types.py`
3. Create schema in `app/schemas/<entity>.py`
4. Create router in `app/routers/<entity>.py`
5. Register router in `app/application.py`
6. Create Alembic migration: `make migration MESSAGE="Add <entity>"`
7. Add tests in `tests/test_<entity>.py`

### Authorization Model
- Entities have `authorized_public` (bool) and `authorized_project_id` (UUID)
- Row-level filtering in `app/db/auth.py`
- Roles: service admin > service maintainer > project admin > project member
- Admin routes under `/admin/<entity>` bypass project filtering

### API Patterns
- POST returns the created entity (status 200)
- GET `/<entity>` returns `{"data": [...], "facets": ...}` with pagination
- GET `/<entity>/{id}` returns single entity
- PATCH `/<entity>/{id}` partial update
- DELETE `/<entity>/{id}` or `/admin/<entity>/{id}`

### Style
- No comments unless complex logic; code should be self-explanatory
- Google-style docstrings where needed
- ruff rules: ALL enabled with specific ignores (see pyproject.toml)
- Line length: 100
- Imports: isort with `known-local-folder = ["tests"]`
