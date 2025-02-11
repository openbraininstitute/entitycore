from contextlib import contextmanager

from app.application import app
from app.routers.auth import check_project_id

BEARER_TOKEN = {"Authorization": "Bearer this is a fake token"}

PROJECT_HEADERS = {
    "virtual-lab-id": "9c6fba01-2c6f-4eac-893f-f0dc665605c5",
    "project-id": "ee86d4a0-eaca-48ca-9788-ddc450250b15",
}

UNRELATED_PROJECT_HEADERS = {
    "virtual-lab-id": "99999999-2c6f-4eac-893f-f0dc665605c5",
    "project-id": "66666666-eaca-48ca-9788-ddc450250b15",
}


@contextmanager
def skip_project_check():
    """Skip checking if Bearer token has access to a the project-id

    Note: Otherwise, the keycloak endpoint is called,
          depending on the config.py::Settings.KEYCLOAK_URL
    """
    orig = dict(app.dependency_overrides)

    def ok():
        return True

    app.dependency_overrides[check_project_id] = ok

    try:
        yield
    finally:
        app.dependency_overrides = orig


def create_reconstruction_morphology_id(
    client, species_id, strain_id, brain_region_id, headers, authorized_public
):
    response = client.post(
        "/reconstruction_morphology/",
        headers=headers,
        json={
            "brain_region_id": brain_region_id,
            "species_id": species_id,
            "strain_id": strain_id,
            "description": "Test Morphology Description",
            "name": "Test Morphology Name",
            "brain_location": {"x": 10, "y": 20, "z": 30},
            "legacy_id": "Test Legacy ID",
            "authorized_public": authorized_public,
        },
    )
    assert response.status_code == 200
    return response.json()["id"]
