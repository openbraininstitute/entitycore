# Entitycore — Agent Rules

## Stack

Python 3.12 | FastAPI | SQLAlchemy sync (psycopg2) | Alembic | Pydantic v2 | boto3 (S3) | JWT auth (Keycloak)
Package manager: uv | Linter: ruff | Type checker: pyright | Line length: 100

## Key Paths

- `app/db/model.py` — all SQLAlchemy models (single file)
- `app/db/types.py` — enums: EntityType, StorageType, etc.
- `app/db/auth.py` — row-level authorization filters
- `app/routers/<entity>.py` — one router per entity
- `app/routers/common.py` — shared router utilities
- `app/schemas/<entity>.py` — Pydantic request/response schemas
- `app/service/<entity>.py` — business logic
- `app/repository/<entity>.py` — DB queries
- `app/dependencies/` — FastAPI dependency injection
- `tests/conftest.py` — shared fixtures
- `tests/utils.py` — test helpers (assert_request, add_db, ClientProxy, check_* functions)
- `tests/test_<entity>.py` — one test file per entity

## Commands

```
make test-docker                          # full suite in Docker (preferred)
make test-local                           # locally (needs: docker compose up --wait db-test)
PYTEST_ADDOPTS="-k test_name" make test-local  # single test
make run-docker                           # service with hot-reload
make format                               # ruff format + fix
make lint                                 # ruff check + pyright
make migration MESSAGE="Add foo"          # create Alembic migration
```

## Code Style Rules

- No comments unless complex logic
- Google-style docstrings only where needed
- ruff ALL rules enabled (see pyproject.toml for ignores)
- Imports: isort with `known-local-folder = ["tests"]`

## Authorization Model

- Every entity has `authorized_public` (bool) + `authorized_project_id` (UUID)
- Row-level filtering in `app/db/auth.py`
- Role hierarchy: service_admin > service_maintainer > project_admin > project_member
- Admin routes: `/admin/<entity>` — bypass project filtering, require service_admin

## API Patterns

- `POST /<entity>` → returns created entity (status 200)
- `GET /<entity>` → `{"data": [...], "facets": ...}` with pagination
- `GET /<entity>/{id}` → single entity
- `PATCH /<entity>/{id}` → partial update
- `DELETE /<entity>/{id}` or `DELETE /admin/<entity>/{id}`

## Adding a New Entity

1. SQLAlchemy model → `app/db/model.py`
2. Enum value → `app/db/types.py` (EntityType)
3. Schema → `app/schemas/<entity>.py`
4. Router → `app/routers/<entity>.py`
5. Register router → `app/application.py`
6. Migration → `make migration MESSAGE="Add <entity>"`
7. Tests → `tests/test_<entity>.py`

## Testing Rules

### DO
- Use `assert_request(client.post, url=ROUTE, json=data)` — asserts status 200 by default
- Use `add_db(db, Model(...))` to insert rows directly into the DB
- Use shared check functions: `check_authorization`, `check_entity_read_many`, `check_entity_update_one`, `check_entity_delete_one`
- Follow the fixture chain: `person_id` → `species_id` → `subject_id` → `brain_region_id`
- Define `ROUTE` and `ADMIN_ROUTE` constants at module top
- Define a `json_data` fixture with the minimal payload for the entity

### DO NOT
- Do NOT use `unittest.TestCase`
- Do NOT create a new `TestClient` — use the `client` or `clients` fixture
- Do NOT mock the database — tests use a real PostgreSQL instance
- Do NOT manually set `created_by_id`/`updated_by_id` when posting via client (auto-set from auth)

### Fixture Reference

| Fixture | Description |
|---------|-------------|
| `client` | Authenticated as user_1 with PROJECT_ID |
| `clients` | ClientProxies namedtuple: user_1, user_2, user_3, no_project, admin, admin_with_project, maintainer_1, maintainer_2, maintainer_3 |
| `db` | SQLAlchemy Session (auto-truncated after each test) |
| `person_id` | Person agent (required for most entities) |
| `species_id` | Created via admin client |
| `brain_region_id` | Requires brain_region_hierarchy_id |
| `subject_id` | Requires species_id, strain_id |
| `license_id` | Created via admin client |
| `morphology_id` | Full cell morphology with mtype classification |

### Test File Template
Use `tests/test_species.py` or `tests/test_subject.py` as reference for new entity tests.

### S3 / Assets in Tests
- Mocked with `moto` (`mock_aws`), session-scoped
- Use `upload_entity_asset(client, entity_type, entity_id, files, label)` to attach files
