from datetime import timedelta
from unittest.mock import ANY

import pytest

from app.db.model import (
    BrainRegion,
    Contribution,
    ExperimentalBoutonDensity,
    Measurement,
    MTypeClass,
    MTypeClassification,
    Species,
    Subject,
)
from app.db.types import EntityType
from app.filters.density import ExperimentalBoutonDensityFilter
from app.schemas.density import ExperimentalBoutonDensityCreate

from .utils import (
    PROJECT_ID,
    add_all_db,
    add_db,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    check_entity_delete_one,
    check_entity_update_one,
    check_missing,
    check_pagination,
)

ROUTE = "/experimental-bouton-density"
ADMIN_ROUTE = "/admin/experimental-bouton-density"


@pytest.fixture
def json_data(brain_region_id, subject_id, license_id):
    return ExperimentalBoutonDensityCreate.model_validate(
        {
            "name": "my-name",
            "description": "my-description",
            "brain_region_id": brain_region_id,
            "subject_id": subject_id,
            "legacy_id": "Test Legacy ID",
            "license_id": license_id,
            "measurements": [
                {
                    "name": "minimum",
                    "unit": "μm",
                    "value": 1.23,
                },
                {
                    "name": "maximum",
                    "unit": "μm",
                    "value": 1.45,
                },
            ],
        }
    ).model_dump(mode="json")


def _assert_read_response(data, json_data):
    assert data["brain_region"]["id"] == json_data["brain_region_id"]
    assert data["subject"]["id"] == json_data["subject_id"]
    assert data["description"] == json_data["description"]
    assert data["name"] == json_data["name"]
    assert data["license"]["name"] == "Test License"
    assert data["type"] == EntityType.experimental_bouton_density
    assert data["created_by"]["id"] == data["updated_by"]["id"]
    assert data["measurements"] == [d | {"id": ANY} for d in json_data["measurements"]]


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model_id(create_id):
    return create_id()


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_update_one(clients, json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={
            "name": "name",
            "description": "description",
            "measurements": [
                {
                    "name": "mean",
                    "unit": "μm",
                    "value": 1.34,
                },
            ],
        },
        optional_payload=None,
    )


def test_user_read_one(client, model_id, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()
    assert len(data["data"]) == 1
    _assert_read_response(data["data"][0], json_data)


def test_admin_read_one(client_admin, model_id, json_data):
    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)


def test_delete_one(
    db,
    clients,
    json_data,
):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={
            ExperimentalBoutonDensity: 1,
        },
        expected_counts_after={
            ExperimentalBoutonDensity: 0,
        },
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(
    client_user_1,
    client_user_2,
    client_no_project,
    json_data,
):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


def test_brain_region_filter(db, client, brain_region_hierarchy_id, subject_id, person_id):
    def create_model_function(_db, name, brain_region_id):
        return ExperimentalBoutonDensity(
            name=name,
            description="my-description",
            brain_region_id=brain_region_id,
            subject_id=subject_id,
            license_id=None,
            authorized_project_id=PROJECT_ID,
            created_by_id=person_id,
            updated_by_id=person_id,
        )

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)


@pytest.fixture
def models(db, json_data, person_id, brain_region_hierarchy_id, agents):
    json_data = json_data.copy()
    measurements = json_data.pop("measurements")
    organization, person, role = agents

    species = add_all_db(
        db,
        [
            Species(
                name=f"species-{i}",
                taxonomy_id=f"taxonomy-{i}",
                created_by_id=person_id,
                updated_by_id=person_id,
                embedding=1536 * [0.1],
            )
            for i in range(3)
        ],
    )
    subjects = add_all_db(
        db,
        [
            Subject(
                name=f"subject-{i}",
                description="my-description",
                species_id=sp.id,
                strain_id=None,
                age_value=timedelta(days=14),
                age_period="postnatal",
                sex="female",
                weight=1.5,
                authorized_public=False,
                authorized_project_id=PROJECT_ID,
                created_by_id=person_id,
                updated_by_id=person_id,
            )
            for i, sp in enumerate(species + species)
        ],
    )

    brain_regions = add_all_db(
        db,
        [
            BrainRegion(
                annotation_value=i,
                acronym=f"acronym-{i}",
                name=f"region-{i}",
                color_hex_triplet="FF0000",
                parent_structure_id=None,
                hierarchy_id=brain_region_hierarchy_id,
                created_by_id=person_id,
                updated_by_id=person_id,
                embedding=1536 * [0.1],
            )
            for i in range(len(subjects))
        ],
    )

    densities = []
    density_ids = [0, 1, 1, 1, 2, 2]
    for i, subject in enumerate(subjects):
        density = add_db(
            db,
            ExperimentalBoutonDensity(
                **json_data
                | {
                    "subject_id": subject.id,
                    "name": f"d-{density_ids[i]}",
                    "created_by_id": person_id,
                    "updated_by_id": person_id,
                    "authorized_project_id": PROJECT_ID,
                    "brain_region_id": brain_regions[i].id,
                }
            ),
        )
        # add measurements
        add_all_db(
            db,
            [
                Measurement(
                    **m
                    | {
                        "value": m["value"] + i,
                        "entity_id": density.id,
                    }
                )
                for i, m in enumerate(measurements)
            ],
        )

        # add contribution
        add_db(
            db,
            Contribution(
                entity_id=density.id,
                role_id=role.id,
                agent_id=(person.id, organization.id)[i % 2],
                created_by_id=person_id,
                updated_by_id=person_id,
            ),
        )

        mtype = add_db(
            db,
            MTypeClass(
                pref_label=f"m{i}",
                alt_label=f"m{i}",
                definition="d",
                created_by_id=person_id,
                updated_by_id=person_id,
            ),
        )
        add_db(
            db,
            MTypeClassification(
                entity_id=density.id,
                mtype_class_id=mtype.id,
                created_by_id=person_id,
                updated_by_id=person_id,
                authorized_public=False,
                authorized_project_id=PROJECT_ID,
            ),
        )

        densities.append(density)

    return species, subjects, densities


def test_filtering(client, models):
    species, _, densities = models

    data = assert_request(client.get, url=ROUTE).json()["data"]
    assert len(data) == len(densities)

    data = assert_request(
        client.get, url=ROUTE, params=f"subject__species__id={species[1].id}"
    ).json()["data"]
    assert len(data) == 2

    data = assert_request(client.get, url=ROUTE, params="subject__species__name=species-2").json()[
        "data"
    ]
    assert len(data) == 2

    data = assert_request(client.get, url=ROUTE, params="subject__species__name=species-2").json()[
        "data"
    ]
    assert len(data) == 2

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"name__in": ["d-1", "d-2"]},
    ).json()["data"]
    assert {d["name"] for d in data} == {"d-1", "d-2"}

    data = assert_request(
        client.get, url=ROUTE, params="contribution__pref_label=test_person_1"
    ).json()["data"]
    assert [d["contributions"][0]["agent"]["pref_label"] for d in data] == ["test_person_1"] * 3

    data = assert_request(
        client.get, url=ROUTE, params="contribution__pref_label=test_organization_1"
    ).json()["data"]
    assert [d["contributions"][0]["agent"]["pref_label"] for d in data] == [
        "test_organization_1"
    ] * 3


def test_sorting(client, models):
    models = models[-1]

    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    # default: ascending by date
    data = req("order_by=creation_date")
    assert len(data) == len(models)
    assert [d["id"] for d in data] == [str(m.id) for m in models]

    # equivalent to above
    data = req({"order_by": ["creation_date"]})
    assert len(data) == len(models)
    assert [d["id"] for d in data] == [str(m.id) for m in models]

    # ascending by date
    data = req("order_by=creation_date")
    assert len(data) == len(models)
    assert [d["id"] for d in data] == [str(m.id) for m in models]

    # equivalent to above
    data = req({"order_by": "+creation_date"})
    assert len(data) == len(models)
    assert [d["id"] for d in data] == [str(m.id) for m in models]

    # descending by date
    data = req("order_by=-creation_date")
    assert len(data) == len(models)
    assert [d["id"] for d in data] == [str(m.id) for m in models][::-1]

    # equivalent to above
    data = req({"order_by": ["-creation_date"]})
    assert len(data) == len(models)
    assert [d["id"] for d in data] == [str(m.id) for m in models][::-1]

    # ascending by name
    data = req("order_by=name")
    assert len(data) == len(models)
    assert [d["name"] for d in data] == [f"d-{i}" for i in (0, 1, 1, 1, 2, 2)]

    # descending by name
    data = req("order_by=-name")
    assert len(data) == len(models)
    assert [d["name"] for d in data] == [f"d-{i}" for i in (2, 2, 1, 1, 1, 0)]

    # ascending by species name
    data = req("order_by=subject__species__name")
    assert [d["subject"]["species"]["name"] for d in data] == [
        f"species-{i}" for i in (0, 0, 1, 1, 2, 2)
    ]

    # descending by species name
    data = req("order_by=-subject__species__name")
    assert [d["subject"]["species"]["name"] for d in data] == [
        f"species-{i}" for i in (2, 2, 1, 1, 0, 0)
    ]

    # ascending by brain region acronym
    data = req("order_by=brain_region__acronym")
    assert [d["brain_region"]["acronym"] for d in data] == [
        f"acronym-{i}" for i in (0, 1, 2, 3, 4, 5)
    ]

    # descending by brain region acronym
    data = req("order_by=-brain_region__acronym")
    assert [d["brain_region"]["acronym"] for d in data] == [
        f"acronym-{i}" for i in (5, 4, 3, 2, 1, 0)
    ]

    # brain region acronym should sort name ties in desc order
    data = req({"order_by": ["+name", "-brain_region__acronym"]})
    assert [d["name"] for d in data] == [f"d-{i}" for i in [0, 1, 1, 1, 2, 2]]
    assert [d["brain_region"]["acronym"] for d in data] == [
        f"acronym-{i}" for i in [0, 3, 2, 1, 5, 4]
    ]

    # brain region acronym should sort name ties in asc order
    data = req({"order_by": ["+name", "+brain_region__acronym"]})
    assert [d["name"] for d in data] == [f"d-{i}" for i in [0, 1, 1, 1, 2, 2]]
    assert [d["brain_region"]["acronym"] for d in data] == [
        f"acronym-{i}" for i in [0, 1, 2, 3, 4, 5]
    ]

    # sort using two cols of the same model
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"order_by": ["+brain_region__name", "+brain_region__acronym"]},
    ).json()["data"]
    assert [d["brain_region"]["name"] for d in data] == [f"region-{i}" for i in [0, 1, 2, 3, 4, 5]]

    # one-to-many with one element
    data = req({"order_by": "mtype__pref_label"})
    assert [d["mtypes"][0]["pref_label"] for d in data] == [f"m{i}" for i in range(6)]

    data = req({"order_by": "-mtype__pref_label"})
    assert [d["mtypes"][0]["pref_label"] for d in data] == [f"m{i}" for i in range(6)][::-1]


def test_sorting_and_filtering(client, models):  # noqa: ARG001
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    for ordering_field in ExperimentalBoutonDensityFilter.Constants.ordering_model_fields:
        data = req({"name__in": ["d-1", "d-0"], "order_by": f"+{ordering_field}"})
        assert len(data) == 4

        data = req({"brain_region__name": "region-1", "order_by": ordering_field})
        assert all(d["brain_region"]["name"] == "region-1" for d in data)

        data = req({"brain_region__name": "", "order_by": ordering_field})
        assert len(data) == 0

        data = req({"brain_region__acronym": "acronym-1", "order_by": ordering_field})
        assert all(d["brain_region"]["acronym"] == "acronym-1" for d in data)

        data = req({"brain_region__acronym": "", "order_by": ordering_field})
        assert len(data) == 0

        data = req(
            {"subject__species__name__in": ["species-1", "species-2"], "order_by": ordering_field}
        )
        assert len(data) == 4

        data = req({"mtype__pref_label__in": ["m1", "m2"], "order_by": ordering_field})
        assert len(data) == 2

    data = req({"name": "d-1", "order_by": "-brain_region__acronym"})
    assert [d["name"] for d in data] == ["d-1", "d-1", "d-1"]
    assert [d["brain_region"]["acronym"] for d in data] == ["acronym-3", "acronym-2", "acronym-1"]

    data = req(
        {
            "subject__species__name__in": ["species-1", "species-2"],
            "order_by": "-brain_region__acronym",
        }
    )
    assert [d["subject"]["species"]["name"] for d in data] == [
        "species-2",
        "species-1",
        "species-2",
        "species-1",
    ]
    assert [d["brain_region"]["acronym"] for d in data] == [
        "acronym-5",
        "acronym-4",
        "acronym-2",
        "acronym-1",
    ]
