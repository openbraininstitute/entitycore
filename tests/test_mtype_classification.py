import pytest

from .utils import (
    assert_request,
    check_creation_fields,
    create_cell_morphology_id,
    create_mtype,
)

ROUTE = "mtype-classification"


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


def test_create_one(client, json_data, morphology_id):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data,
    ).json()
    assert data["entity_id"] == json_data["entity_id"]
    assert data["mtype_class_id"] == json_data["mtype_class_id"]
    check_creation_fields(data)

    # check that mtype classification worked and morph now has a custom mtype
    data = assert_request(
        client.get,
        url=f"/cell-morphology/{morphology_id}",
    ).json()["mtypes"]

    assert json_data["mtype_class_id"] in {m["id"] for m in data}


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
