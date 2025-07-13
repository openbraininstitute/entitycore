from datetime import timedelta
from time import sleep

import pytest

from app.db.model import (
    BrainRegion,
    Contribution,
    ETypeClass,
    ETypeClassification,
    ExperimentalNeuronDensity,
    MTypeClass,
    MTypeClassification,
    Species,
    Subject,
)
from app.db.types import EntityType
from app.filters.density import ExperimentalNeuronDensityFilter

from .utils import (
    PROJECT_ID,
    add_all_db,
    add_db,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    check_missing,
    check_pagination,
    count_db_class,
)

ROUTE = "/experimental-neuron-density"
MODEL_CLASS = ExperimentalNeuronDensity


@pytest.fixture
def json_data(brain_region_id, subject_id, license_id):
    return {
        "brain_region_id": str(brain_region_id),
        "subject_id": subject_id,
        "description": "my-description",
        "name": "my-name",
        "legacy_id": "Test Legacy ID",
        "license_id": license_id,
    }


def _assert_read_response(data, json_data):
    assert data["brain_region"]["id"] == json_data["brain_region_id"]
    assert data["subject"]["id"] == json_data["subject_id"]
    assert data["description"] == json_data["description"]
    assert data["name"] == json_data["name"]
    assert data["license"]["name"] == "Test License"
    assert data["type"] == EntityType.experimental_neuron_density
    assert data["created_by"]["id"] == data["updated_by"]["id"]


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


def test_read_one(client, model_id, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()
    assert len(data["data"]) == 1
    _assert_read_response(data["data"][0], json_data)


def test_delete_one(
    db,
    client,
    client_admin,
    model_id,
    person_id,
    role_id,
):
    add_db(
        db,
        Contribution(
            agent_id=person_id,
            role_id=role_id,
            entity_id=model_id,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    mtype = add_db(
        db,
        MTypeClass(
            pref_label="m1",
            alt_label="m1",
            definition="e1d",
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    add_db(
        db,
        MTypeClassification(
            entity_id=model_id,
            mtype_class_id=mtype.id,
            created_by_id=person_id,
            updated_by_id=person_id,
            authorized_public=False,
            authorized_project_id=PROJECT_ID,
        ),
    )

    assert count_db_class(db, ExperimentalNeuronDensity) == 1
    assert count_db_class(db, Contribution) == 1
    assert count_db_class(db, MTypeClass) == 1
    assert count_db_class(db, MTypeClassification) == 1

    data = assert_request(client.delete, url=f"{ROUTE}/{model_id}", expected_status_code=403).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, ExperimentalNeuronDensity) == 0
    assert count_db_class(db, Contribution) == 0
    assert count_db_class(db, MTypeClass) == 1
    assert count_db_class(db, MTypeClassification) == 0


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
        return MODEL_CLASS(
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
    organization, person, role = agents

    species = add_all_db(
        db,
        [
            Species(
                name=f"species-{i}",
                taxonomy_id=f"taxonomy-{i}",
                created_by_id=person_id,
                updated_by_id=person_id,
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
            )
            for i in range(len(subjects))
        ],
    )

    densities = []
    density_ids = [0, 1, 1, 1, 2, 2]
    for i, subject in enumerate(subjects):
        density = add_db(
            db,
            ExperimentalNeuronDensity(
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
        etype = add_db(
            db,
            ETypeClass(
                pref_label=f"e{i}",
                alt_label=f"e{i}",
                definition="d",
                created_by_id=person_id,
                updated_by_id=person_id,
            ),
        )
        add_db(
            db,
            ETypeClassification(
                entity_id=density.id,
                etype_class_id=etype.id,
                created_by_id=person_id,
                updated_by_id=person_id,
                authorized_public=False,
                authorized_project_id=PROJECT_ID,
            ),
        )

        densities.append(density)

        # to vary the creation date
        sleep(0.01)

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

    # backwards compat
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"name__in": "d-1,d-2"},
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

    data = req({"order_by": "etype__pref_label"})
    assert [d["etypes"][0]["pref_label"] for d in data] == [f"e{i}" for i in range(6)]

    data = req({"order_by": "-etype__pref_label"})
    assert [d["etypes"][0]["pref_label"] for d in data] == [f"e{i}" for i in range(6)][::-1]


def test_sorting_and_filtering(client, models):  # noqa: ARG001
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    for ordering_field in ExperimentalNeuronDensityFilter.Constants.ordering_model_fields:
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

        data = req({"etype__pref_label__in": ["e1", "e2"], "order_by": ordering_field})
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
