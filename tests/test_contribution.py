import pytest

from app.db.model import Contribution, Organization, Person, Role

from .utils import (
    BEARER_TOKEN,
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_HEADERS,
    UNRELATED_PROJECT_HEADERS,
    add_db,
    assert_dict_equal,
    assert_request,
    create_reconstruction_morphology_id,
)

ROUTE = "/contribution"
ROUTE_MORPH = "/reconstruction-morphology"


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

    response = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "agent_id": str(person_id),
            "role_id": str(role_id),
            "entity_id": str(reconstruction_morphology_id),
        },
    )
    data = response.json()
    assert_dict_equal(
        data,
        {
            "agent.id": str(person_id),
            "agent.givenName": "jd",
            "agent.pref_label": "jd courcol",
            "agent.type": "person",
            "role.id": str(role_id),
            "role.name": "important role",
            "role.role_id": "important role id",
            "entity.id": reconstruction_morphology_id,
        },
    )

    contribution_id = data["id"]

    response = assert_request(
        client.get,
        url=f"{ROUTE}/{contribution_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert_dict_equal(
        response.json(),
        {
            "agent.id": str(person_id),
            "agent.givenName": "jd",
            "agent.familyName": "courcol",
            "agent.type": "person",
            "role.id": str(role_id),
            "role.name": "important role",
            "role.role_id": "important role id",
            "entity.id": reconstruction_morphology_id,
            "id": contribution_id,
        },
    )

    response = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "agent_id": str(organization_id),
            "role_id": str(role_id),
            "entity_id": str(reconstruction_morphology_id),
        },
    )
    assert_dict_equal(
        response.json(),
        {
            "agent.id": str(organization_id),
            "agent.pref_label": "ACME",
            "agent.alternative_name": "A Company Making Everything",
            "agent.type": "organization",
        },
    )

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    assert len(response.json()["data"]) == 2

    response = assert_request(
        client.get,
        url=f"{ROUTE_MORPH}/{reconstruction_morphology_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    data = response.json()
    assert "contributions" in data
    assert len(data["contributions"]) == 2

    response = assert_request(
        client.get,
        url=ROUTE_MORPH,
        params={"with_facets": True},
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    data = response.json()["data"]
    assert len(data) == 1
    assert len(data[0]["contributions"]) == 2

    facets = response.json()["facets"]
    assert len(facets["contribution"]) == 2
    assert facets["contribution"] == [
        {"id": str(organization_id), "label": "ACME", "type": "organization", "count": 1},
        {"id": str(person_id), "label": "jd courcol", "type": "person", "count": 1},
    ]


@pytest.mark.usefixtures("skip_project_check")
@pytest.mark.parametrize(
    ("route_id", "expected_status_code"),
    [
        (MISSING_ID, 404),
        (MISSING_ID_COMPACT, 404),
        ("42424242", 422),
        ("notanumber", 422),
    ],
)
def test_missing(client, route_id, expected_status_code):
    assert_request(
        client.get,
        url=f"{ROUTE}/{route_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        expected_status_code=expected_status_code,
    )


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

    # can't attach contributions to projects unrelated to us
    response = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "agent_id": str(person_id),
            "role_id": str(role_id),
            "entity_id": str(inaccessible_entity_id),
        },
        expected_status_code=404,
    )

    response = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | UNRELATED_PROJECT_HEADERS,
        json={
            "agent_id": str(person_id),
            "role_id": str(role_id),
            "entity_id": str(inaccessible_entity_id),
        },
        expected_status_code=200,
    )
    inaccessible_annotation_id = response.json()["id"]

    response = assert_request(
        client.get,
        url=f"{ROUTE}/{inaccessible_annotation_id}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        expected_status_code=404,
    )

    public_entity_id = create_reconstruction_morphology_id(
        client,
        species_id,
        strain_id,
        brain_region_id,
        headers=BEARER_TOKEN | UNRELATED_PROJECT_HEADERS,
        authorized_public=True,
    )
    # can't attach contributions to projects unrelated to us, even if public
    response = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        json={
            "agent_id": str(person_id),
            "role_id": str(role_id),
            "entity_id": str(public_entity_id),
        },
        expected_status_code=404,
    )

    public_obj = assert_request(
        client.post,
        url=ROUTE,
        headers=BEARER_TOKEN | UNRELATED_PROJECT_HEADERS,
        json={
            "agent_id": str(person_id),
            "role_id": str(role_id),
            "entity_id": str(public_entity_id),
        },
        expected_status_code=200,
    )
    public_obj = public_obj.json()

    # can get the contribution if the entity is public
    response = assert_request(
        client.get,
        url=f"{ROUTE}/{public_obj['id']}",
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        expected_status_code=200,
    )

    response = assert_request(
        client.get,
        url=ROUTE,
        headers=BEARER_TOKEN | PROJECT_HEADERS,
        expected_status_code=200,
    )
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

    response = assert_request(
        client.get,
        url=ROUTE_MORPH,
        params={"with_facets": True, "page_size": 10},
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    data = response.json()
    facets = data["facets"]
    assert facets == {
        "contribution": [
            {"count": 6, "id": str(org.id), "label": "org_pref_label", "type": "organization"},
            {"count": 9, "id": str(person.id), "label": "person_pref_label", "type": "person"},
        ],
        "mtype": [],
        "species": [
            {"count": 12, "id": str(species_id), "label": "Test Species", "type": "species"}
        ],
        "strain": [{"count": 12, "id": str(strain_id), "label": "Test Strain", "type": "strain"}],
    }
    assert len(data["data"]) == 10
    expected_indexes = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]

    expected_morphology_ids = [morphology_ids[i] for i in expected_indexes]
    assert [item["id"] for item in data["data"]] == expected_morphology_ids

    expected_contribution_sizes = [contribution_sizes[i] for i in expected_indexes]
    assert [len(item["contributions"]) for item in data["data"]] == expected_contribution_sizes

    response = assert_request(
        client.get,
        url=f"{ROUTE_MORPH}",
        params={"with_facets": True, "contribution__pref_label": "person_pref_label"},
        headers=BEARER_TOKEN | PROJECT_HEADERS,
    )
    data = response.json()
    facets = data["facets"]
    assert facets == {
        "contribution": [
            {"count": 9, "id": str(person.id), "label": "person_pref_label", "type": "person"}
        ],
        "mtype": [],
        "species": [
            {"count": 9, "id": str(species_id), "label": "Test Species", "type": "species"}
        ],
        "strain": [{"count": 9, "id": str(strain_id), "label": "Test Strain", "type": "strain"}],
    }
    assert len(data["data"]) == 9
    expected_indexes = [11, 10, 6, 5, 4, 3, 2, 1, 0]

    expected_morphology_ids = [morphology_ids[i] for i in expected_indexes]
    assert [item["id"] for item in data["data"]] == expected_morphology_ids

    expected_contribution_sizes = [contribution_sizes[i] for i in expected_indexes]
    assert [len(item["contributions"]) for item in data["data"]] == expected_contribution_sizes
