import pytest

from .utils import (
    assert_request,
    check_creation_fields,
    create_cell_morphology_id,
    create_etype,
)

ROUTE = "etype-classification"


@pytest.fixture
def custom_etype(db, person_id):
    return create_etype(
        db,
        pref_label="my-custom-etype",
        alt_label="my-custom-etype",
        definition="My custom etype",
        created_by_id=person_id,
    )


@pytest.fixture
def unauthorized_morph_id(client_user_2, brain_region_id, subject_id):
    return create_cell_morphology_id(
        client_user_2,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )


@pytest.fixture
def json_data(emodel_id, custom_etype):
    return {
        "entity_id": str(emodel_id),
        "etype_class_id": str(custom_etype.id),
        "authorized_public": True,
    }


def test_create_one(client, json_data, emodel_id):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data,
    ).json()
    assert data["entity_id"] == json_data["entity_id"]
    assert data["etype_class_id"] == json_data["etype_class_id"]
    check_creation_fields(data)

    # check that mtype classification worked and morph now has a custom mtype
    data = assert_request(
        client.get,
        url=f"/emodel/{emodel_id}",
    ).json()["etypes"]

    assert json_data["etype_class_id"] in {m["id"] for m in data}


def test_create_one__unauthorized_entity(client_user_1, unauthorized_morph_id, json_data):
    # Doesn't matter it isn't an emodel because the check is done first
    json_data |= {"entity_id": str(unauthorized_morph_id)}

    data = assert_request(
        client_user_1.post, url=ROUTE, json=json_data, expected_status_code=403
    ).json()
    assert data["details"] == f"Cannot access entity {unauthorized_morph_id}"


def test_do_not_allow_private_classification(client, db, person_id, emodel_id):
    etype = create_etype(
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
            "entity_id": str(emodel_id),
            "etype_class_id": str(etype.id),
            "authorized_public": False,
        },
        expected_status_code=400,
    ).json()
    assert (
        data["details"] == "Private classifications are not supported. Use authorized_public=True"
    )
