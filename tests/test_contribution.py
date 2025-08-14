from app.db.model import CellMorphology, Contribution, Organization, Role, Subject

from .utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    add_db,
    check_creation_fields,
    create_cell_morphology_id,
    create_person,
)

ROUTE = "/contribution"
ROUTE_MORPH = "/cell-morphology"


def test_create_contribution(
    client,
    person_id,
    organization_id,
    role_id,
    subject_id,
    brain_region_id,
):
    cell_morphology_id = create_cell_morphology_id(
        client,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )

    response = client.post(
        ROUTE,
        json={
            "agent_id": str(person_id),
            "role_id": str(role_id),
            "entity_id": str(cell_morphology_id),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["id"] == str(person_id)
    assert data["agent"]["given_name"] == "jd"
    assert data["agent"]["family_name"] == "courcol"
    assert data["agent"]["pref_label"] == "jd courcol"
    assert data["agent"]["type"] == "person"
    assert data["role"]["id"] == str(role_id)
    assert data["role"]["name"] == "important role"
    assert data["role"]["role_id"] == "important role id"
    assert data["entity"]["id"] == cell_morphology_id
    check_creation_fields(data)

    contribution_id = data["id"]

    response = client.get(f"{ROUTE}/{contribution_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["id"] == str(person_id)
    assert data["agent"]["given_name"] == "jd"
    assert data["agent"]["family_name"] == "courcol"
    assert data["agent"]["type"] == "person"
    assert data["role"]["id"] == str(role_id)
    assert data["role"]["name"] == "important role"
    assert data["role"]["role_id"] == "important role id"
    assert data["entity"]["id"] == cell_morphology_id
    assert data["id"] == contribution_id
    check_creation_fields(data)

    response = client.post(
        ROUTE,
        json={
            "agent_id": str(organization_id),
            "role_id": str(role_id),
            "entity_id": str(cell_morphology_id),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["id"] == str(organization_id)
    assert data["agent"]["pref_label"] == "ACME"
    assert data["agent"]["alternative_name"] == "A Company Making Everything"
    assert data["agent"]["type"] == "organization"
    check_creation_fields(data)

    response = client.get(ROUTE)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2

    response = client.get(f"{ROUTE_MORPH}/{cell_morphology_id}")
    assert response.status_code == 200
    data = response.json()
    assert "contributions" in data
    assert len(data["contributions"]) == 2

    response = client.get(ROUTE_MORPH, params={"with_facets": True})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert len(data[0]["contributions"]) == 2

    facets = response.json()["facets"]
    assert len(facets["contribution"]) == 2
    assert facets["contribution"] == [
        {"id": str(organization_id), "label": "ACME", "type": "organization", "count": 1},
        {"id": str(person_id), "label": "jd courcol", "type": "person", "count": 1},
    ]


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422


def test_authorization(
    client_user_1,
    client_user_2,
    client_no_project,
    brain_region_id,
    subject_id,
    person_id,
    role_id,
):
    inaccessible_entity_id = create_cell_morphology_id(
        client_user_2,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )

    response = client_user_1.post(
        ROUTE,
        json={
            "agent_id": str(person_id),
            "role_id": str(role_id),
            "entity_id": str(inaccessible_entity_id),
        },
    )
    # can't attach contributions to projects unrelated to us
    assert response.status_code == 404

    response = client_user_2.post(
        ROUTE,
        json={
            "agent_id": str(person_id),
            "role_id": str(role_id),
            "entity_id": str(inaccessible_entity_id),
        },
    )
    assert response.status_code == 200
    inaccessible_annotation_id = response.json()["id"]

    response = client_user_1.get(f"{ROUTE}/{inaccessible_annotation_id}")
    assert response.status_code == 404

    public_entity_id = create_cell_morphology_id(
        client_user_2,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=True,
    )
    response = client_user_1.post(
        ROUTE,
        json={
            "agent_id": str(person_id),
            "role_id": str(role_id),
            "entity_id": str(public_entity_id),
        },
    )
    # can't attach contributions to projects unrelated to us, even if public
    assert response.status_code == 404

    public_obj = client_user_2.post(
        ROUTE,
        json={
            "agent_id": str(person_id),
            "role_id": str(role_id),
            "entity_id": str(public_entity_id),
        },
    )
    assert public_obj.status_code == 200
    public_obj = public_obj.json()

    response = client_user_1.get(f"{ROUTE}/{public_obj['id']}")
    # can get the contribution if the entity is public
    assert response.status_code == 200

    response = client_user_1.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1  # only public entity is available
    assert data[0]["id"] == public_obj["id"]
    assert data[0]["entity"]["id"] == public_entity_id
    assert data[0]["entity"]["authorized_public"]

    # only return public results
    response = client_no_project.get(ROUTE)
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == public_obj["id"]


def test_contribution_facets(
    db,
    client,
    subject_id,
    brain_region_id,
    person_id,
):
    subject = db.get(Subject, subject_id)
    species_id = str(subject.species.id)
    strain_id = str(subject.strain.id)

    person = create_person(
        db,
        given_name="GivenName",
        family_name="FamilyName",
        pref_label="person_pref_label",
        created_by_id=person_id,
    )

    person_role = add_db(
        db,
        Role(
            name="PersonRoleName",
            role_id="role_id",
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )

    org = add_db(
        db,
        Organization(
            pref_label="org_pref_label",
            alternative_name="org_alt_name",
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    org_role = add_db(
        db,
        Role(
            name="OrgRoleName",
            role_id="role_id_org",
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )

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
        cell_morphology_id = create_cell_morphology_id(
            client,
            subject_id=subject_id,
            brain_region_id=brain_region_id,
            name=f"TestMorphologyName{i}",
            authorized_public=False,
        )
        morphology_ids.append(cell_morphology_id)
        contribution_sizes.append(len(contributions))
        for agent, agent_role in contributions:
            add_db(
                db,
                Contribution(
                    agent_id=agent.id,
                    role_id=agent_role.id,
                    entity_id=cell_morphology_id,
                    created_by_id=person_id,
                    updated_by_id=person_id,
                ),
            )

    assert len(morphology_ids) == 12
    assert contribution_sizes == [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2]

    agent = db.get(CellMorphology, morphology_ids[0]).created_by
    """
    response = client.get(ROUTE_MORPH, params={"with_facets": True, "page_size": 10})
    assert response.status_code == 200
    data = response.json()
    facets = data["facets"]
    assert facets == {
        "brain_region": [
            {"count": 12, "id": str(brain_region_id), "label": "RedRegion", "type": "brain_region"},
        ],
        "contribution": [
            {"count": 6, "id": str(org.id), "label": "org_pref_label", "type": "organization"},
            {"count": 9, "id": str(person.id), "label": "person_pref_label", "type": "person"},
        ],
        "mtype": [],
        "species": [
            {"count": 12, "id": str(species_id), "label": "Test Species", "type": "species"}
        ],
        "strain": [{"count": 12, "id": str(strain_id), "label": "Test Strain", "type": "strain"}],
        "created_by": [
            {"count": 12, "id": str(agent.id), "label": agent.pref_label, "type": agent.type}
        ],
        "updated_by": [
            {"count": 12, "id": str(agent.id), "label": agent.pref_label, "type": agent.type}
        ],
    }
    assert len(data["data"]) == 10
    expected_indexes = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]

    expected_morphology_ids = [morphology_ids[i] for i in expected_indexes]
    assert [item["id"] for item in data["data"]] == expected_morphology_ids

    expected_contribution_sizes = [contribution_sizes[i] for i in expected_indexes]
    assert [len(item["contributions"]) for item in data["data"]] == expected_contribution_sizes
    """
    response = client.get(
        f"{ROUTE_MORPH}",
        params={"with_facets": True, "contribution__pref_label": "person_pref_label"},
    )
    assert response.status_code == 200
    data = response.json()
    facets = data["facets"]
    assert facets == {
        "brain_region": [
            {"count": 9, "id": str(brain_region_id), "label": "RedRegion", "type": "brain_region"},
        ],
        "contribution": [
            {"count": 9, "id": str(person.id), "label": "person_pref_label", "type": "person"}
        ],
        "mtype": [],
        "species": [
            {"count": 9, "id": str(species_id), "label": "Test Species", "type": "subject.species"}
        ],
        "strain": [
            {"count": 9, "id": str(strain_id), "label": "Test Strain", "type": "subject.strain"}
        ],
        "created_by": [
            {"count": 9, "id": str(agent.id), "label": agent.pref_label, "type": str(agent.type)}
        ],
        "updated_by": [
            {"count": 9, "id": str(agent.id), "label": agent.pref_label, "type": str(agent.type)}
        ],
    }
    assert len(data["data"]) == 9
    expected_indexes = [11, 10, 6, 5, 4, 3, 2, 1, 0]

    expected_morphology_ids = [morphology_ids[i] for i in expected_indexes]
    assert [item["id"] for item in data["data"]] == expected_morphology_ids

    expected_contribution_sizes = [contribution_sizes[i] for i in expected_indexes]
    assert [len(item["contributions"]) for item in data["data"]] == expected_contribution_sizes
