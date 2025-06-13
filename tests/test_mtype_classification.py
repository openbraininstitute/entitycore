import uuid

import pytest

from .utils import (
    PROJECT_ID,
    UNRELATED_PROJECT_ID,
    assert_request,
    check_creation_fields,
    create_mtype,
    create_mtype_classification,
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
def json_data(morphology_id, custom_mtype):
    return {
        "entity_id": str(morphology_id),
        "mtype_class_id": str(custom_mtype.id),
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


@pytest.fixture
def public_morphology_id(client_user_1, species_id, brain_region_id, strain_id):
    return create_reconstruction_morphology_id(
        client_user_1,
        species_id=species_id,
        brain_region_id=brain_region_id,
        strain_id=strain_id,
        authorized_public=True,
    )


def test_mtype__do_not_show_private_classifications(db, person_id, client_user_1, client_user_2, public_morphology_id):

    mtypes = [
        create_mtype(
            db,
            pref_label=name,
            alt_label=name,
            definition=name,
            created_by_id=person_id,
        )
        for name in ["custom1", "custom2", "custom3"]
    ]

    # The user registers a classification with their project id
    c1 = assert_request(
        client_user_1.post,
        url=ROUTE,
        json={
            "entity_id": str(public_morphology_id),
            "mtype_class_id": str(mtypes[0].id),
            "authorized_public": False,
        }
    )
    # An unrelated user registers a classification that is public
    c2 = assert_request(
        client_user_2.post,
        url=ROUTE,
        json={
            "entity_id": str(public_morphology_id),
            "mtype_class_id": str(mtypes[1].id),
            "authorized_public": True,
        }
    )
    # An unrelated user registers a classification that is private to their project
    c3 = assert_request(
        client_user_2.post,
        url=ROUTE,
        json={
            "entity_id": str(public_morphology_id),
            "mtype_class_id": str(mtypes[2].id),
            "authorized_public": False,
        }
    )

    # The user now fetches the morphology and they should get only the mtypes registered with either
    # an authorized or public classification.

    data = assert_request(
        client_user_1.get,
        url=f"/reconstruction-morphology/{public_morphology_id}",
    ).json()["mtypes"]

    mtype_ids = {m["id"] for m in data}

    assert str(mtypes[0].id) in mtype_ids
    assert str(mtypes[1].id) in mtype_ids
    assert str(mtypes[2].id) not in mtype_ids
