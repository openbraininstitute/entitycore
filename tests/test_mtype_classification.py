import pytest

from app.db.model import CellMorphology, MTypeClass, MTypeClassification

from .utils import (
    assert_request,
    check_creation_fields,
    count_db_class,
    create_cell_morphology_id,
    create_mtype,
)

ROUTE = "mtype-classification"
ADMIN_ROUTE = "/admin/mtype-classification"


@pytest.fixture
def custom_mtype(db, person_id):
    return create_mtype(
        db,
        pref_label="my-custom-mtype",
        alt_label="my-custom-mtype",
        definition="My custom mtype",
        created_by_id=person_id,
    )


@pytest.fixture
def unauthorized_morph_id(subject_id, client_user_2, brain_region_id):
    return create_cell_morphology_id(
        client_user_2,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )


@pytest.fixture
def json_data(morphology_id, custom_mtype):
    return {
        "entity_id": str(morphology_id),
        "mtype_class_id": str(custom_mtype.id),
        "authorized_public": True,
    }


@pytest.fixture
def model_id(client, json_data):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data,
    ).json()
    return data["id"]


def _assert_read_schema(data, json_data):
    assert data["entity_id"] == json_data["entity_id"]
    assert data["mtype_class_id"] == json_data["mtype_class_id"]


def test_create_one(client, json_data, morphology_id):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data,
    ).json()
    _assert_read_schema(data, json_data)
    check_creation_fields(data)

    # check that mtype classification worked and morph now has a custom mtype
    data = assert_request(
        client.get,
        url=f"/cell-morphology/{morphology_id}",
    ).json()["mtypes"]

    assert json_data["mtype_class_id"] in {m["id"] for m in data}


def test_read_one(client, json_data, model_id):
    data = assert_request(
        client.get,
        url=f"{ROUTE}/{model_id}",
    ).json()
    _assert_read_schema(data, json_data)


def test_read_many(client, json_data, model_id):
    data = assert_request(
        client.get,
        url=ROUTE,
    ).json()["data"]
    _assert_read_schema(data[0], json_data)
    assert data[0]["id"] == str(model_id)


def test_filtering(client, model_id, morphology_id, custom_mtype):
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"entity_id": str(morphology_id), "mtype_class_id": str(custom_mtype.id)},
    ).json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == str(model_id)


def test_delete_one(db, client, client_admin, json_data):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data,
    ).json()

    model_id = data["id"]

    assert count_db_class(db, CellMorphology) == 1
    assert count_db_class(db, MTypeClass) == 2
    assert count_db_class(db, MTypeClassification) == 2

    data = assert_request(
        client.delete, url=f"{ADMIN_ROUTE}/{model_id}", expected_status_code=403
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ADMIN_ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, CellMorphology) == 1
    assert count_db_class(db, MTypeClass) == 2
    assert count_db_class(db, MTypeClassification) == 1


def test_create_one__unauthorized_entity(client_user_1, unauthorized_morph_id, json_data):
    json_data |= {"entity_id": str(unauthorized_morph_id)}

    data = assert_request(
        client_user_1.post, url=ROUTE, json=json_data, expected_status_code=403
    ).json()
    assert data["details"] == f"Cannot access entity {unauthorized_morph_id}"


@pytest.fixture
def public_morphology_id(client_user_1, subject_id, brain_region_id):
    return create_cell_morphology_id(
        client_user_1,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=True,
    )


def test_do_not_allow_private_classification(client, db, person_id, public_morphology_id):
    mtype = create_mtype(
        db,
        pref_label="c1",
        alt_label="c1",
        definition="c1",
        created_by_id=person_id,
    )
    data = assert_request(
        client.post,
        url=ROUTE,
        json={
            "entity_id": str(public_morphology_id),
            "mtype_class_id": str(mtype.id),
            "authorized_public": False,
        },
        expected_status_code=400,
    ).json()
    assert (
        data["details"] == "Private classifications are not supported. Use authorized_public=True"
    )
