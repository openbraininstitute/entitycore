import pytest

from .utils import (
    BEARER_TOKEN,
    PROJECT_HEADERS,
    UNRELATED_PROJECT_HEADERS,
    create_reconstruction_morphology_id,
)

ROUTE = "/contribution/"


@pytest.mark.usefixtures("skip_project_check")
def test_create_contribution(
    client,
    person_id,
    organization_id,
    role_id,
    species_id,
    strain_id,
    brain_region_id,
):
    reconstruction_morphology_id = create_reconstruction_morphology_id(
        client,
        species_id,
        strain_id,
        brain_region_id,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        authorized_public=False,
    )

    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "agent_id": person_id,
            "role_id": role_id,
            "entity_id": reconstruction_morphology_id,
        },
    )
    response.raise_for_status()
    data = response.json()
    assert data["agent"]["id"] == person_id
    assert data["agent"]["givenName"] == "jd"
    assert data["agent"]["familyName"] == "courcol"
    assert data["agent"]["pref_label"] == "jd courcol"
    assert data["agent"]["type"] == "person"
    assert data["role"]["id"] == role_id
    assert data["role"]["name"] == "important role"
    assert data["role"]["role_id"] == "important role id"
    assert data["entity"]["id"] == reconstruction_morphology_id

    contribution_id = data["id"]

    response = client.get(f"{ROUTE}{contribution_id}", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["id"] == person_id
    assert data["agent"]["givenName"] == "jd"
    assert data["agent"]["familyName"] == "courcol"
    assert data["agent"]["type"] == "person"
    assert data["role"]["id"] == role_id
    assert data["role"]["name"] == "important role"
    assert data["role"]["role_id"] == "important role id"
    assert data["entity"]["id"] == reconstruction_morphology_id
    assert data["id"] == contribution_id

    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "agent_id": organization_id,
            "role_id": role_id,
            "entity_id": reconstruction_morphology_id,
        },
    )
    response.raise_for_status()
    data = response.json()
    assert data["agent"]["id"] == organization_id
    assert data["agent"]["pref_label"] == "ACME"
    assert data["agent"]["alternative_name"] == "A Company Making Everything"
    assert data["agent"]["type"] == "organization"

    response = client.get(
        "/contribution/",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert len(response.json()) == 2

    response = client.get(
        f"/reconstruction_morphology/{reconstruction_morphology_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    response.raise_for_status()
    data = response.json()
    assert "contributors" in data
    assert len(data["contributors"]) == 2

    response = client.get(
        "/reconstruction_morphology/",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    response.raise_for_status()
    data = response.json()["data"]
    assert len(data) == 1
    assert len(data[0]["contributors"]) == 2

    facets = response.json()["facets"]
    assert len(facets["contributors"]) == 2
    assert facets["contributors"] == [
        {"count": 1, "id": 2, "label": "ACME", "type": "organization"},
        {"count": 1, "id": 1, "label": "jd courcol", "type": "person"},
    ]


@pytest.mark.usefixtures("skip_project_check")
def test_missing(client):
    response = client.get(ROUTE + "12345", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 404

    response = client.get(ROUTE + "not_a_contribution_id", headers=BEARER_TOKEN | PROJECT_HEADERS)
    assert response.status_code == 422


@pytest.mark.usefixtures("skip_project_check")
def test_authorization(client, brain_region_id, species_id, strain_id, person_id, role_id):
    inaccessible_entity_id = create_reconstruction_morphology_id(
        client,
        species_id,
        strain_id,
        brain_region_id,
        headers=BEARER_TOKEN | UNRELATED_PROJECT_HEADERS,
        authorized_public=False,
    )

    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "agent_id": person_id,
            "role_id": role_id,
            "entity_id": inaccessible_entity_id,
        },
    )
    # can't attach contributions to projects unrelated to us
    assert response.status_code == 404

    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | UNRELATED_PROJECT_HEADERS,
        json={
            "agent_id": person_id,
            "role_id": role_id,
            "entity_id": inaccessible_entity_id,
        },
    )
    assert response.status_code == 200
    inaccessible_annotation_id = response.json()["id"]
    response = client.get(
        f"{ROUTE}{inaccessible_annotation_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert response.status_code == 404

    public_entity_id = create_reconstruction_morphology_id(
        client,
        species_id,
        strain_id,
        brain_region_id,
        headers=BEARER_TOKEN | UNRELATED_PROJECT_HEADERS,
        authorized_public=True,
    )
    response = client.post(
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={"agent_id": person_id, "role_id": role_id, "entity_id": public_entity_id},
    )
    # can't attach contributions to projects unrelated to us, even if public
    assert response.status_code == 404

    public_obj = client.post(
        ROUTE,
        headers=BEARER_TOKEN | UNRELATED_PROJECT_HEADERS,
        json={
            "agent_id": person_id,
            "role_id": role_id,
            "entity_id": public_entity_id,
        },
    )
    assert public_obj.status_code == 200
    public_obj = public_obj.json()

    response = client.get(
        f"{ROUTE}{public_obj['id']}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    # can get the contributor if the entity is public
    assert response.status_code == 200

    response = client.get(
        f"{ROUTE}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # only public entity is available
    assert data[0]["id"] == public_obj["id"]
    assert data[0]["entity"]["id"] == public_entity_id
    assert data[0]["entity"]["authorized_public"]
