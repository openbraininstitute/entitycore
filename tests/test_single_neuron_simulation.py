import pytest

from app.db.model import MEModel

from .utils import BEARER_TOKEN, PROJECT_HEADERS

ROUTE = "/single-neuron-simulation"


@pytest.mark.usefixtures("skip_project_check")
def test_single_neuron_simulation(client, db, brain_region_id):
    row = MEModel(
        name="my-me-model",
        description="my-description",
        status="foo",
        validated=False,
        brain_region_id=brain_region_id,
        authorized_project_id=PROJECT_HEADERS["project-id"],
    )

    db.add(row)
    db.commit()
    db.refresh(row)
    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "name": "foo",
            "description": "my-description",
            "injectionLocation": ["soma[0]"],
            "recordingLocation": ["soma[0]_0.5"],
            "me_model_id": row.id,
            "status": "foo",
            "seed": 1,
            "authorized_public": False,
            "brain_region_id": brain_region_id,
        },
    )
    assert response.status_code == 200, response.content

    data = response.json()
    assert data["brain_region"]["id"] == brain_region_id, (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "foo"
    assert data["injectionLocation"] == ["soma[0]"]
    assert data["recordingLocation"] == ["soma[0]_0.5"]
    # assert data["me_model"]["id"] == me_model_id, f"Failed to get id frmo me model; {data}"
    assert data["status"] == "foo"
    assert data["authorized_project_id"] == PROJECT_HEADERS["project-id"]

    response = client.get(f"{ROUTE}/{data['id']}", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 200, response.content
    assert data["brain_region"]["id"] == brain_region_id, (
        f"Failed to get id for reconstruction morphology: {data}"
    )
    assert data["description"] == "my-description"
    assert data["name"] == "foo"
    assert data["injectionLocation"] == ["soma[0]"]
    assert data["recordingLocation"] == ["soma[0]_0.5"]
    # assert data["me_model"]["id"] == me_model_id, f"Failed to get id frmo me model; {data}"
    assert data["status"] == "foo"
    assert data["authorized_project_id"] == PROJECT_HEADERS["project-id"]
