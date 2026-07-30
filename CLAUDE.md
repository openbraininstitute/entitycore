<!-- AUTO-GENERATED from AGENTS.md — do not edit directly, run: make sync-rules -->

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
- `app/filters/<entity>.py` — fastapi-filter definitions (query params, ordering, nested filters)
- `app/filters/base.py` — `CustomFilter` base class (extends fastapi-filter with aliases, nested sort, ilike search)
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
4. Filter → `app/filters/<entity>.py` (extend `CustomFilter`, add mixins for nested filtering)
5. Router → `app/routers/<entity>.py`
6. Register router → `app/application.py`
7. Migration → `make migration MESSAGE="Add <entity>"`
8. Tests → `tests/test_<entity>.py`

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

## Release (entitycore)

Triggered by the user message **release**.

### Calver format

`YYYY.M.N` — year, month (no zero-padding), sequential counter within the month starting at `0`.
Examples: `2026.7.13`, `2026.8.0`.

### Next tag algorithm

1. `YEAR` = current UTC year, `MONTH` = current UTC month (1–12).
2. List tags matching `YEAR.MONTH.*`; take the highest `N`.
3. Next tag = `YEAR.MONTH.(N+1)`, or `YEAR.MONTH.0` if none exist for this month.

### Workflow (approval required)

**Do not create or push a tag until the user explicitly approves.**

1. Ensure `main` is checked out and up to date with `origin/main`.
2. Find the latest tag: `git describe --tags --abbrev=0`.
3. **Show a release preview** and stop for approval:
   - Proposed tag (from the algorithm above).
   - Commits since the latest tag: `git log <latest-tag>..main --oneline`.
   - Image that will be built: `public.ecr.aws/openbraininstitute/entitycore:<tag>` (see `.github/workflows/publish.yml`).
4. Wait for explicit user approval (e.g. "yes", "approve", "go ahead").
5. After approval only:
   ```bash
   git tag <tag>
   git push origin <tag>
   ```
6. Confirm the `Build and publish the Docker image` workflow started for the new tag.
7. If the user only said **release**, tell them they can run **deploy** once the image is published.
   If they also said **deploy**, continue with the Deploy workflow below using the new tag (do not wait for a separate "deploy" message).

## Release and deploy (combined)

Triggered when the user message includes both **release** and **deploy** (e.g. "release and deploy").

1. Run the full **Release** workflow (preview → wait for approval → tag → push).
2. Immediately after the tag is pushed, run the **Deploy** workflow for that same tag (default `staging` unless the user named environments).
3. Return both results: the new tag / publish workflow status, and the terraform PR URL.
4. Note that the Docker image may still be building when the deploy PR is opened; merging the terraform PR should wait until the image is in ECR.

## Deploy (entitycore → terraform)

Triggered by the user message **deploy**, or as the second step of **release and deploy**.

Requires a **released** entitycore tag. Prefer waiting until the Docker image is in ECR before merging the terraform PR; opening the PR may happen right after the tag is pushed when combined with release. If no tag is given, use the latest git tag on `main`.

### Target repository

`https://github.com/openbraininstitute/aws-terraform-deployment`

### Image URL format

```
public.ecr.aws/openbraininstitute/entitycore:<tag>
```

Update the `entitycore_svc_image_url` variable in the relevant `*.tfvars` files.

| File | Environment |
|------|-------------|
| `staging.tfvars` | staging |
| `production.tfvars` | production |
| `sandbox-nse.tfvars` | sandbox NSE |
| `sandbox-hpc.tfvars` | sandbox HPC |
| `sandbox-benchmarks.tfvars` | sandbox benchmarks |

**Ask which environment(s) to update** if the user did not specify. Default to `staging` only.

### Workflow

1. Confirm the tag and target environment(s).
2. Clone or update the terraform repo (sibling dir or temp):
   ```bash
   gh repo clone openbraininstitute/aws-terraform-deployment /tmp/aws-terraform-deployment
   cd /tmp/aws-terraform-deployment && git checkout main && git pull
   ```
3. Create branch `entitycore-<tag>` (or `bump-entitycore-<tag>`).
4. In each chosen `*.tfvars`, set:
   ```
   entitycore_svc_image_url = "public.ecr.aws/openbraininstitute/entitycore:<tag>"
   ```
5. Commit, push, and open a PR:
   ```bash
   git checkout -b entitycore-<tag>
   git add <changed-tfvars>
   git commit -m "Update entitycore to <tag>"
   git push -u origin entitycore-<tag>
   gh pr create --title "Update entitycore to <tag>" --body "Bump entitycore_svc_image_url to <tag>."
   ```
6. Return the PR URL to the user.
