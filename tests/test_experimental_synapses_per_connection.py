import itertools

import pytest

from app.db.model import (
    BrainRegion,
    Contribution,
    ExperimentalSynapsesPerConnection,
    MTypeClass,
)
from app.db.types import EntityType
from app.filters.density import ExperimentalSynapsesPerConnectionFilter

from .utils import (
    add_db,
    assert_request,
    check_authorization,
    check_brain_region_filter,
    check_missing,
    check_pagination,
    count_db_class,
    create_brain_region,
    create_mtype,
    delete_entity_classifications,
    delete_entity_contributions,
)

MODEL = ExperimentalSynapsesPerConnection
ROUTE = "/experimental-synapses-per-connection"
ADMIN_ROUTE = "/admin/experimental-synapses-per-connection"


@pytest.fixture
def json_data(brain_region_id, subject_id, license_id, mtype_class_id):
    return {
        "brain_region_id": str(brain_region_id),
        "subject_id": subject_id,
        "description": "my-description",
        "name": "my-name",
        "legacy_id": "Test Legacy ID",
        "license_id": license_id,
        "pre_region_id": brain_region_id,
        "post_region_id": brain_region_id,
        "pre_mtype_id": mtype_class_id,
        "post_mtype_id": mtype_class_id,
    }


def _assert_read_response(data, json_data):
    assert data["brain_region"]["id"] == json_data["brain_region_id"]
    assert data["subject"]["id"] == json_data["subject_id"]
    assert data["description"] == json_data["description"]
    assert data["name"] == json_data["name"]
    assert data["license"]["name"] == "Test License"
    assert data["pre_mtype"]["id"] == json_data["pre_mtype_id"]
    assert data["post_mtype"]["id"] == json_data["post_mtype_id"]
    assert data["pre_region"]["id"] == json_data["pre_region_id"]
    assert data["post_region"]["id"] == json_data["post_region_id"]
    assert data["type"] == EntityType.experimental_synapses_per_connection
    assert data["created_by"]["id"] == data["updated_by"]["id"]


@pytest.fixture
def create(client, json_data):
    def _create(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()

    return _create


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def create_db(db, create_id):
    def _create_db(**kwargs):
        return db.get(MODEL, create_id(**kwargs))

    return _create_db


@pytest.fixture
def model_id(create_id):
    return create_id()


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_update_one(client, model_id):
    new_name = "my_new_name"
    new_description = "my_new_description"

    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{model_id}",
        json={
            "name": new_name,
            "description": new_description,
        },
    ).json()

    assert data["name"] == new_name
    assert data["description"] == new_description


def test_update_one__public(client, json_data):
    # make private entity public
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data
        | {
            "authorized_public": True,
        },
    ).json()

    # should not be allowed to update it once public
    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{data['id']}",
        json={"name": "foo"},
        expected_status_code=404,
    ).json()
    assert data["error_code"] == "ENTITY_NOT_FOUND"


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

    assert count_db_class(db, ExperimentalSynapsesPerConnection) == 1
    assert count_db_class(db, Contribution) == 1
    assert count_db_class(db, MTypeClass) == 1
    assert count_db_class(db, BrainRegion) == 1

    data = assert_request(
        client.delete, url=f"{ADMIN_ROUTE}/{model_id}", expected_status_code=403
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    delete_entity_contributions(client_admin, ROUTE, model_id)
    delete_entity_classifications(client, client_admin, model_id)

    data = assert_request(client_admin.delete, url=f"{ADMIN_ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, ExperimentalSynapsesPerConnection) == 0
    assert count_db_class(db, Contribution) == 0
    assert count_db_class(db, MTypeClass) == 1
    assert count_db_class(db, BrainRegion) == 1


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


def test_brain_region_filter(
    db,
    client,
    create_db,
    brain_region_hierarchy_id,
):
    def create_model_function(_db, name, brain_region_id):
        return create_db(name=name, brain_region_id=str(brain_region_id))

    check_brain_region_filter(ROUTE, client, db, brain_region_hierarchy_id, create_model_function)


@pytest.fixture
def models(db, brain_region_hierarchy_id, create, person_id):
    pre_region_ids = [
        create_brain_region(
            db,
            hierarchy_id=brain_region_hierarchy_id,
            annotation_value=i,
            name=f"pre-r{i}",
            created_by_id=person_id,
        ).id
        for i in [0, 1]
    ]
    post_region_ids = [
        create_brain_region(
            db,
            hierarchy_id=brain_region_hierarchy_id,
            annotation_value=i,
            name=f"post-r{i}",
            created_by_id=person_id,
        ).id
        for i in [2, 3]
    ]
    pre_mtype_ids = [
        create_mtype(db, pref_label=f"pre-m{i}", created_by_id=person_id).id for i in [0, 1]
    ]
    post_mtype_ids = [
        create_mtype(db, pref_label=f"post-m{i}", created_by_id=person_id).id for i in [2, 3]
    ]

    synapses_per_connection = []
    for i, (pre_region_id, post_region_id, pre_mtype_id, post_mtype_id) in enumerate(
        itertools.product(pre_region_ids, post_region_ids, pre_mtype_ids, post_mtype_ids)
    ):
        syn = create(
            name=f"s{i}",
            description=f"d{i}",
            pre_mtype_id=str(pre_mtype_id),
            post_mtype_id=str(post_mtype_id),
            pre_region_id=str(pre_region_id),
            post_region_id=str(post_region_id),
        )

        synapses_per_connection.append(syn)

    return synapses_per_connection


def test_filtering__one_entry(client, model_id, mtype_class_id):
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"pre_mtype__id": str(model_id)},
    ).json()["data"]

    assert len(data) == 0

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"pre_mtype__id": str(mtype_class_id)},
    ).json()["data"]

    assert len(data) == 1
    assert data[0]["pre_mtype"]["id"] == str(mtype_class_id)


def test_filtering__many_entries(client, models):
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"pre_mtype__pref_label": "pre-m0"},
    ).json()["data"]

    n_elements = len(data)
    n_expected = sum(1 for m in models if m["pre_mtype"]["pref_label"] == "pre-m0")
    assert n_elements == n_expected

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"post_mtype__pref_label": "post-m0"},
    ).json()["data"]

    n_elements = len(data)
    n_expected = sum(1 for m in models if m["post_mtype"]["pref_label"] == "post-m0")
    assert n_elements == n_expected

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"pre_region__acronym": "pre-r0"},
    ).json()["data"]

    n_elements = len(data)
    n_expected = sum(1 for m in models if m["pre_region"]["acronym"] == "pre-r0")
    assert n_elements == n_expected

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"post_region__acronym": "post-r0"},
    ).json()["data"]

    n_elements = len(data)
    n_expected = sum(1 for m in models if m["post_region"]["acronym"] == "post-r0")
    assert n_elements == n_expected


def test_facets(client, models):
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"with_facets": True},
    ).json()

    counts = {
        "pre-m0": 0,
        "pre-m1": 0,
        "post-m2": 0,
        "post-m3": 0,
        "pre-r0": 0,
        "pre-r1": 0,
        "post-r2": 0,
        "post-r3": 0,
    }
    for model in models:
        counts[model["pre_mtype"]["pref_label"]] += 1
        counts[model["post_mtype"]["pref_label"]] += 1
        counts[model["pre_region"]["name"]] += 1
        counts[model["post_region"]["name"]] += 1

    n_elements = len(data["data"])
    assert "facets" in data
    facets = data["facets"]
    assert facets["species"][0]["count"] == n_elements
    assert facets["pre_mtype"][0]["label"] == "pre-m0"
    assert facets["pre_mtype"][0]["count"] == counts["pre-m0"]
    assert facets["pre_mtype"][1]["label"] == "pre-m1"
    assert facets["pre_mtype"][1]["count"] == counts["pre-m1"]
    assert facets["post_mtype"][0]["label"] == "post-m2"
    assert facets["post_mtype"][0]["count"] == counts["post-m2"]
    assert facets["post_mtype"][1]["label"] == "post-m3"
    assert facets["post_mtype"][1]["count"] == counts["post-m3"]
    assert facets["pre_region"][0]["label"] == "pre-r0"
    assert facets["pre_region"][0]["count"] == counts["pre-r0"]
    assert facets["pre_region"][1]["label"] == "pre-r1"
    assert facets["pre_region"][1]["count"] == counts["pre-r1"]
    assert facets["post_region"][0]["label"] == "post-r2"
    assert facets["post_region"][0]["count"] == counts["post-r2"]
    assert facets["post_region"][1]["label"] == "post-r3"
    assert facets["post_region"][1]["count"] == counts["post-r3"]


def test_sorting_and_filtering(client, models):
    n_models = len(models)

    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    for ordering_field in ExperimentalSynapsesPerConnectionFilter.Constants.ordering_model_fields:
        data = req({"name__in": ["s1", "s0"], "order_by": f"+{ordering_field}"})
        assert len(data) == 2

        data = req({"brain_region__name": "region-1", "order_by": ordering_field})
        assert all(d["brain_region"]["name"] == "region-1" for d in data)

        data = req({"brain_region__name": "", "order_by": ordering_field})
        assert len(data) == 0

        data = req({"brain_region__acronym": "acronym-1", "order_by": ordering_field})
        assert all(d["brain_region"]["acronym"] == "acronym-1" for d in data)

        data = req({"brain_region__acronym": "", "order_by": ordering_field})
        assert len(data) == 0

        data = req({"subject__species__name__in": ["Test Species"], "order_by": ordering_field})
        assert len(data) == n_models

        data = req({"post_mtype__pref_label": "post-m2", "order_by": ordering_field})
        assert [d["post_mtype"]["pref_label"] for d in data] == ["post-m2"] * len(data)
