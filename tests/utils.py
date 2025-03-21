from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials

from app.application import app
from app.dependencies.auth import AuthHeader, verify_project_context
from app.schemas.base import ProjectContext

TEST_DATA_DIR = Path(__file__).parent / "data"

BEARER_TOKEN = {"Authorization": "Bearer this is a fake token"}
VIRTUAL_LAB_ID = "9c6fba01-2c6f-4eac-893f-f0dc665605c5"
PROJECT_ID = "ee86d4a0-eaca-48ca-9788-ddc450250b15"

MISSING_ID = "12345678-1234-5678-1234-567812345678"
MISSING_ID_COMPACT = MISSING_ID.replace("-", "")

PROJECT_HEADERS = {
    "virtual-lab-id": VIRTUAL_LAB_ID,
    "project-id": PROJECT_ID,
}

UNRELATED_PROJECT_HEADERS = {
    "virtual-lab-id": "99999999-2c6f-4eac-893f-f0dc665605c5",
    "project-id": "66666666-eaca-48ca-9788-ddc450250b15",
}


@contextmanager
def skip_project_check():
    """Skip checking if Bearer token has access to the project-id

    Note: Otherwise, the keycloak endpoint is called,
          depending on the config.py::Settings.KEYCLOAK_URL
    """

    def mock_verify_project_context(
        project_context: Annotated[ProjectContext, Header()],
        token: Annotated[HTTPAuthorizationCredentials, Depends(AuthHeader)],
    ) -> ProjectContext:
        assert f"{token.scheme} {token.credentials}" == BEARER_TOKEN["Authorization"]
        return project_context

    orig = dict(app.dependency_overrides)
    app.dependency_overrides[verify_project_context] = mock_verify_project_context

    try:
        yield
    finally:
        app.dependency_overrides = orig


def create_reconstruction_morphology_id(
    client,
    species_id,
    strain_id,
    brain_region_id,
    headers,
    authorized_public,
    name="Test Morphology Name",
    description="Test Morphology Description",
):
    response = client.post(
        "/reconstruction-morphology",
        headers=headers,
        json={
            "name": name,
            "description": description,
            "brain_region_id": str(brain_region_id) if isinstance(brain_region_id, int) else None,
            "species_id": str(species_id) if species_id else None,
            "strain_id": str(strain_id) if strain_id else None,
            "location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": "Test Legacy ID",
            "authorized_public": authorized_public,
        },
    )

    assert response.status_code == 200
    return response.json()["id"]


def add_db(db, row):
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def add_all_db(db, rows):
    db.add_all(rows)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def assert_request(client_method, *, expected_status_code=200, **kwargs):
    response = client_method(**kwargs)
    assert response.status_code == expected_status_code, response.content
    return response
