import pytest

from app.db.model import MTypeClass, MTypeClassification, ReconstructionMorphology

from .utils import (
    assert_request,
    check_creation_fields,
    count_db_class,
    create_mtype,
    create_reconstruction_morphology_id,
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
def unauthorized_morph_id(species_id, client_user_2, brain_region_id):
    return create_reconstruction_morphology_id(
        client_user_2,
        species_id=species_id,
        strain_id=None,
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
        url=f"/reconstruction-morphology/{morphology_id}",
    ).json()["mtypes"]

    assert json_data["mtype_class_id"] in {m["id"] for m in data}


def test_delete_one(db, client, client_admin, json_data):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data,
    ).json()

    model_id = data["id"]

    assert count_db_class(db, ReconstructionMorphology) == 1
    assert count_db_class(db, MTypeClass) == 2
    assert count_db_class(db, MTypeClassification) == 2

    data = assert_request(client.delete, url=f"{ROUTE}/{model_id}", expected_status_code=403).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, ReconstructionMorphology) == 1
    assert count_db_class(db, MTypeClass) == 2
    assert count_db_class(db, MTypeClassification) == 1


def test_create_one__unauthorized_entity(client_user_1, unauthorized_morph_id, json_data):
    json_data |= {"entity_id": str(unauthorized_morph_id)}

    data = assert_request(
        client_user_1.post, url=ROUTE, json=json_data, expected_status_code=403
    ).json()
    assert data["details"] == f"Cannot access entity {unauthorized_morph_id}"


@pytest.fixture
def public_morphology_id(client_user_1, species_id, brain_region_id, strain_id):
    return create_reconstruction_morphology_id(
        client_user_1,
        species_id=species_id,
        brain_region_id=brain_region_id,
        strain_id=strain_id,
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
