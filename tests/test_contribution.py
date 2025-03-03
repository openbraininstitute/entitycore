import pytest

from app.db.model import (
    Contribution,
    Organization,
    Person,
    Role,
)

from .utils import (
    BEARER_TOKEN,
    PROJECT_HEADERS,
    UNRELATED_PROJECT_HEADERS,
    add_db,
    create_reconstruction_morphology_id,
)

ROUTE = "/contribution/"
ROUTE_MORPH = "/reconstruction-morphology/"


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
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert len(response.json()["data"]) == 2

    response = client.get(
        f"{ROUTE_MORPH}{reconstruction_morphology_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    response.raise_for_status()
    data = response.json()
    assert "contributions" in data
    assert len(data["contributions"]) == 2

    response = client.get(
        ROUTE_MORPH,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    response.raise_for_status()
    data = response.json()["data"]
    assert len(data) == 1
    assert len(data[0]["contributions"]) == 2

    facets = response.json()["facets"]
    assert len(facets["contributions"]) == 2
    assert facets["contributions"] == [
        {"id": 2, "label": "ACME", "type": "organization", "count": 1},
        {"id": 1, "label": "jd courcol", "type": "person", "count": 1},
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
        ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1  # only public entity is available
    assert data[0]["id"] == public_obj["id"]
    assert data[0]["entity"]["id"] == public_entity_id
    assert data[0]["entity"]["authorized_public"]


@pytest.mark.usefixtures("skip_project_check")
def test_contribution_facets(
    db,
    client,
    species_id,
    strain_id,
    brain_region_id,
):
    person = add_db(
        db, Person(givenName="givenName", familyName="FamilyName", pref_label="person_pref_label")
    )
    person_role = add_db(db, Role(name="PersonRoleName", role_id="role_id"))

    org = add_db(db, Organization(pref_label="org_pref_label", alternative_name="org_alt_name"))
    org_role = add_db(db, Role(name="OrgRoleName", role_id="role_id_org"))

    morphology_ids = []
    contribution_sizes = []  # len of contributions for each morphology
    for i, contributions in enumerate(
        [
            [(person, person_role), (org, org_role)],
            [(person, person_role)],
            [(person, person_role)],
            [(person, person_role)],
            [(person, person_role)],
            [(person, person_role)],
            [(person, person_role)],
            [(org, org_role)],
            [(org, org_role)],
            [(org, org_role)],
            [(person, person_role), (org, org_role)],
            [(person, person_role), (org, org_role)],
        ]
    ):
        reconstruction_morphology_id = create_reconstruction_morphology_id(
            client,
            species_id,
            strain_id,
            brain_region_id,
            headers=BEARER_TOKEN | PROJECT_HEADERS,
            name=f"TestMorphologyName{i}",
            authorized_public=False,
        )
        morphology_ids.append(reconstruction_morphology_id)
        contribution_sizes.append(len(contributions))
        for agent, agent_role in contributions:
            add_db(
                db,
                Contribution(
                    agent_id=agent.id, role_id=agent_role.id, entity_id=reconstruction_morphology_id
                ),
            )

    assert len(morphology_ids) == 12
    assert contribution_sizes == [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2]

    response = client.get(
        ROUTE_MORPH,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    data = response.json()
    facets = data["facets"]
    assert facets == {
        "contributions": [
            {"count": 6, "id": 2, "label": "org_pref_label", "type": "organization"},
            {"count": 9, "id": 1, "label": "person_pref_label", "type": "person"},
        ],
        "mtypes": [],
        "species": [{"count": 12, "id": 1, "label": "Test Species", "type": "species"}],
        "strain": [{"count": 12, "id": 1, "label": "Test Strain", "type": "strain"}],
    }
    assert len(data["data"]) == 10
    expected_indexes = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]

    expected_morphology_ids = [morphology_ids[i] for i in expected_indexes]
    assert [item["id"] for item in data["data"]] == expected_morphology_ids

    expected_contribution_sizes = [contribution_sizes[i] for i in expected_indexes]
    assert [len(item["contributions"]) for item in data["data"]] == expected_contribution_sizes

    response = client.get(
        f"{ROUTE_MORPH}?contributor__pref_label=person_pref_label",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    data = response.json()
    facets = data["facets"]
    assert facets == {
        "contributions": [{"count": 9, "id": 1, "label": "person_pref_label", "type": "person"}],
        "mtypes": [],
        "species": [{"count": 9, "id": 1, "label": "Test Species", "type": "species"}],
        "strain": [{"count": 9, "id": 1, "label": "Test Strain", "type": "strain"}],
    }
    assert len(data["data"]) == 9
    expected_indexes = [11, 10, 6, 5, 4, 3, 2, 1, 0]

    expected_morphology_ids = [morphology_ids[i] for i in expected_indexes]
    assert [item["id"] for item in data["data"]] == expected_morphology_ids

    expected_contribution_sizes = [contribution_sizes[i] for i in expected_indexes]
    assert [len(item["contributions"]) for item in data["data"]] == expected_contribution_sizes
