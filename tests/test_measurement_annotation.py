from copy import deepcopy
from unittest.mock import ANY

import pytest

from .utils import (
    assert_request,
    assert_response,
    check_missing,
    create_cell_morphology_id,
)

ROUTE = "/measurement-annotation"
ADMIN_ROUTE = "/admin/measurement-annotation"
LABEL_ROUTE = "/measurement-label"
MORPHOLOGY_ROUTE = "/cell-morphology"
ENTITY_TYPE = "cell_morphology"


@pytest.fixture
def measurement_labels(client_admin, person_id):
    labels = []
    for i in range(2):
        response = client_admin.post(
            LABEL_ROUTE,
            json={
                "entity_type": ENTITY_TYPE,
                "pref_label": f"pref_label_{i}",
                "definition": "",
                "created_by_id": str(person_id),
                "updated_by_id": str(person_id),
            },
        )
        assert response.status_code == 200, f"Failed to create measurement label: {response.text}"
        data = response.json()
        labels.append(data["pref_label"])
    return labels


@pytest.fixture
def json_data(morphology_id, measurement_labels):
    return {
        "entity_type": ENTITY_TYPE,
        "entity_id": str(morphology_id),
        "measurement_kinds": [
            {
                "pref_label": measurement_labels[0],
                "structural_domain": "axon",
                "measurement_items": [
                    {
                        "name": "mean",
                        "unit": "μm",
                        "value": 54.2,
                    },
                    {
                        "name": "median",
                        "unit": "μm",
                        "value": 44.6,
                    },
                ],
            },
        ],
    }


def _assert_read_response(data, json_data):
    assert "id" in data
    assert data["entity_type"] == json_data["entity_type"]
    assert data["entity_id"] == json_data["entity_id"]
    assert data["measurement_kinds"] == json_data["measurement_kinds"]


def test_read_many(
    clients, subject_id, brain_region_id, measurement_labels, cell_morphology_protocol_id
):

    route = ROUTE
    admin_route = ADMIN_ROUTE

    # register entities with users in different projects
    c1_id = create_cell_morphology_id(
        clients.user_1,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        cell_morphology_protocol_id=cell_morphology_protocol_id,
        authorized_public=False,
    )
    c2_id = create_cell_morphology_id(
        clients.user_1,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        cell_morphology_protocol_id=cell_morphology_protocol_id,
        authorized_public=True,
    )
    c3_id = create_cell_morphology_id(
        clients.user_2,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        cell_morphology_protocol_id=cell_morphology_protocol_id,
        authorized_public=False,
    )
    c4_id = create_cell_morphology_id(
        clients.user_2,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        cell_morphology_protocol_id=cell_morphology_protocol_id,
        authorized_public=True,
    )

    json_data = {
        "entity_type": ENTITY_TYPE,
        "measurement_kinds": [
            {
                "pref_label": measurement_labels[0],
                "structural_domain": "axon",
                "measurement_items": [
                    {
                        "name": "mean",
                        "unit": "μm",
                        "value": 54.2,
                    },
                    {
                        "name": "median",
                        "unit": "μm",
                        "value": 44.6,
                    },
                ],
            },
        ],
    }

    u1_private = assert_request(
        clients.user_1.post,
        url=route,
        json=json_data | {"entity_id": c1_id},
    ).json()
    u1_public = assert_request(
        clients.user_1.post,
        url=ROUTE,
        json=json_data | {"entity_id": c2_id},
    ).json()
    u2_private = assert_request(
        clients.user_2.post,
        url=ROUTE,
        json=json_data | {"entity_id": c3_id},
    ).json()
    u2_public = assert_request(
        clients.user_2.post,
        url=ROUTE,
        json=json_data | {"entity_id": c4_id},
    ).json()

    def req(client, client_route, expected_status_code=200):
        return assert_request(
            client.get, url=client_route, expected_status_code=expected_status_code
        ).json()

    # user1 can get their entities and user2's public
    results = req(clients.user_1, route)["data"]
    assert {r["id"] for r in results} == {u1_private["id"], u1_public["id"], u2_public["id"]}

    # user not allowed using admin route
    data = req(clients.user_1, admin_route, expected_status_code=403)
    assert data["message"] == "Service admin role required"

    # same for user2
    results = req(clients.user_2, route)["data"]
    assert {r["id"] for r in results} == {u2_private["id"], u2_public["id"], u1_public["id"]}

    # user not allowed using admin route
    data = req(clients.user_2, admin_route, expected_status_code=403)
    assert data["message"] == "Service admin role required"

    # admin using the user route has access only to public entities (no project headers)
    results = req(clients.admin, route)["data"]
    assert {r["id"] for r in results} == {u1_public["id"], u2_public["id"]}

    # admin on admin route can get them all
    results = req(clients.admin, admin_route)["data"]
    assert {r["id"] for r in results} == {
        u1_private["id"],
        u1_public["id"],
        u2_private["id"],
        u2_public["id"],
    }


def test_update_one(clients, json_data, subject_id, brain_region_id, cell_morphology_protocol_id):
    old_morph_id = json_data["entity_id"]

    new_morph_id = create_cell_morphology_id(
        clients.user_1,
        subject_id,
        brain_region_id,
        cell_morphology_protocol_id=cell_morphology_protocol_id,
        authorized_public=True,
    )

    model_id = assert_request(clients.user_1.post, url=ROUTE, json=json_data).json()["id"]

    patch_data = {
        "entity_id": str(new_morph_id),
    }
    data = assert_request(clients.user_1.patch, url=f"{ROUTE}/{model_id}", json=patch_data).json()
    assert data["entity_id"] == patch_data["entity_id"]

    # user 2 shouldn't have access to user's 1 entity to update.
    data = assert_request(
        clients.user_2.patch, url=f"{ROUTE}/{model_id}", json=patch_data, expected_status_code=404
    ).json()
    assert data["error_code"] == "ENTITY_NOT_FOUND"

    patch_data = {
        "entity_id": str(old_morph_id),
    }

    # users shouldn't have access to service admin endpoints
    data = assert_request(
        clients.user_1.patch, url=f"{ADMIN_ROUTE}/{model_id}", json={}, expected_status_code=403
    ).json()
    assert data["message"] == "Service admin role required"

    data = assert_request(
        clients.admin.patch, url=f"{ADMIN_ROUTE}/{model_id}", json=patch_data
    ).json()
    assert data["entity_id"] == patch_data["entity_id"]


def _get_request_payload_1(entity_id, labels):
    return {
        "entity_type": ENTITY_TYPE,
        "entity_id": entity_id,
        "measurement_kinds": [
            {
                "pref_label": labels[0],
                "structural_domain": "axon",
                "measurement_items": [
                    {
                        "name": "mean",
                        "unit": "μm",
                        "value": 54.2,
                    },
                    {
                        "name": "median",
                        "unit": "μm",
                        "value": 44.6,
                    },
                ],
            },
            {
                "pref_label": labels[1],
                "structural_domain": "soma",
                "measurement_items": [
                    {
                        "name": "mean",
                        "unit": "μm²",
                        "value": 97.6,
                    },
                    {
                        "name": "median",
                        "unit": "μm²",
                        "value": 73.86,
                    },
                ],
            },
        ],
    }


def _get_request_payload_2(entity_id, labels):
    return {
        "entity_type": ENTITY_TYPE,
        "entity_id": entity_id,
        "measurement_kinds": [
            {
                "pref_label": labels[0],
                "structural_domain": "axon",
                "measurement_items": [
                    {
                        "name": "mean",
                        "unit": "μm",
                        "value": 154.2,
                    },
                    {
                        "name": "median",
                        "unit": "μm",
                        "value": 144.6,
                    },
                ],
            },
        ],
    }


def _get_return_payload(request_payload):
    payload = deepcopy(request_payload) | {
        "id": ANY,
        "creation_date": ANY,
        "update_date": ANY,
    }
    return payload


def test_create_and_retrieve(
    clients, subject_id, brain_region_id, measurement_labels, cell_morphology_protocol_id
):
    client = clients.user_1

    morphology_id = create_cell_morphology_id(
        client,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        cell_morphology_protocol_id=cell_morphology_protocol_id,
        authorized_public=False,
    )
    request_payload_1 = _get_request_payload_1(entity_id=morphology_id, labels=measurement_labels)
    expected_payload_1 = _get_return_payload(request_payload=request_payload_1)

    # create a valid measurement annotation
    response = client.post(ROUTE, json=request_payload_1)
    assert_response(response, expected_status_code=200)
    data = response.json()
    assert data == expected_payload_1
    measurement_annotation_id_1 = data["id"]

    # read the resource
    response = client.get(f"{ROUTE}/{measurement_annotation_id_1}")
    assert_response(response, expected_status_code=200)
    data = response.json()
    assert data == expected_payload_1

    response = clients.admin.get(f"{ADMIN_ROUTE}/{measurement_annotation_id_1}")
    assert_response(response, expected_status_code=200)
    data = response.json()
    assert data == expected_payload_1

    # read the morphology without measurements
    response = client.get(f"{MORPHOLOGY_ROUTE}/{morphology_id}")
    assert_response(response, expected_status_code=200)
    assert "measurement_annotation" not in response.json()

    # read the morphology with measurements
    response = client.get(
        f"{MORPHOLOGY_ROUTE}/{morphology_id}",
        params={"expand": "measurement_annotation"},
    )
    assert_response(response, expected_status_code=200)
    data = response.json()
    assert "measurement_annotation" in data

    # delete the 1st annotation
    response = client.delete(f"{ROUTE}/{measurement_annotation_id_1}")
    assert_response(response, expected_status_code=200)
    data = response.json()
    assert data == expected_payload_1

    # create a 2nd annotation
    request_payload_2 = _get_request_payload_2(entity_id=morphology_id, labels=measurement_labels)
    response = client.post(ROUTE, json=request_payload_2)
    assert_response(response, expected_status_code=200)
    data = response.json()
    measurement_annotation_id_2 = data["id"]

    # read the morphology with the new measurements
    response = client.get(
        f"{MORPHOLOGY_ROUTE}/{morphology_id}",
        params={"expand": "measurement_annotation"},
    )
    assert_response(response, expected_status_code=200)
    data = response.json()
    assert data["measurement_annotation"]["id"] == measurement_annotation_id_2
    assert data["measurement_annotation"]["entity_id"] == data["id"] == morphology_id

    # filter the annotations
    query_params = {
        "measurement_kind__pref_label": measurement_labels[0],
        "measurement_item__name": "mean",
        "measurement_item__value__gte": 154,
        "measurement_item__value__lte": 155,
    }
    response = client.get(f"{ROUTE}", params=query_params)
    assert_response(response, expected_status_code=200)
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == measurement_annotation_id_2

    # filter by entity_type
    query_params = {"entity_type": ENTITY_TYPE}
    response = client.get(f"{ROUTE}", params=query_params)
    assert_response(response, expected_status_code=200)
    data = response.json()
    assert len(data["data"]) == 1

    # filter the morphology by annotation
    query_params = {
        "measurement_kind__pref_label": measurement_labels[0],
        "measurement_item__name": "mean",
        "measurement_item__value__gte": 154,
        "measurement_item__value__lte": 155,
    }
    response = client.get(f"{MORPHOLOGY_ROUTE}", params=query_params)
    assert_response(response, expected_status_code=200)
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == morphology_id

    # filter the morphology by annotation, no results
    query_params = {
        "measurement_kind__pref_label": measurement_labels[0],
        "measurement_item__name": "mean",
        "measurement_item__value__gte": 54,
        "measurement_item__value__lte": 55,
    }
    response = client.get(f"{MORPHOLOGY_ROUTE}", params=query_params)
    assert_response(response, expected_status_code=200)
    data = response.json()
    assert len(data["data"]) == 0

    invalid_labels = ["pref_label_0", "invalid_label_0"]
    invalid_payload = _get_request_payload_1(entity_id=morphology_id, labels=invalid_labels)

    # try to create an annotation with invalid labels
    response = client.post(ROUTE, json=invalid_payload)
    assert_response(response, expected_status_code=422)
    data = response.json()
    assert data == {
        "error_code": "INVALID_REQUEST",
        "message": "Invalid measurement labels for entity type cell_morphology",
        "details": {
            "allowed_labels": ["pref_label_0", "pref_label_1"],
            "invalid_labels": ["invalid_label_0"],
        },
    }


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(
    client_user_1,
    client_user_2,
    client_no_project,
    subject_id,
    brain_region_id,
    cell_morphology_protocol_id,
    measurement_labels,
):
    morphology_id_public = create_cell_morphology_id(
        client_user_1,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        cell_morphology_protocol_id=cell_morphology_protocol_id,
        authorized_public=True,
    )

    response = client_user_1.post(
        ROUTE,
        json=_get_request_payload_1(entity_id=morphology_id_public, labels=measurement_labels),
    )
    assert_response(response, expected_status_code=200)
    measurement_annotation_id_public = response.json()["id"]

    morphology_id_inaccessible = create_cell_morphology_id(
        client_user_2,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        cell_morphology_protocol_id=cell_morphology_protocol_id,
        authorized_public=False,
    )

    # try to add annotation to inaccessible cell
    response = client_user_1.post(
        ROUTE,
        json=_get_request_payload_1(
            entity_id=morphology_id_inaccessible, labels=measurement_labels
        ),
    )
    assert_response(response, expected_status_code=404)

    # succeed to add annotation to inaccessible cell with a different client
    response = client_user_2.post(
        ROUTE,
        json=_get_request_payload_1(
            entity_id=morphology_id_inaccessible, labels=measurement_labels
        ),
    )
    assert_response(response, expected_status_code=200)

    response = client_user_1.get(f"{ROUTE}/{response.json()['id']}")
    assert_response(response, expected_status_code=404)

    morphology_id_public_inaccessible = create_cell_morphology_id(
        client_user_2,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        cell_morphology_protocol_id=cell_morphology_protocol_id,
        authorized_public=True,
    )
    response = client_user_1.post(
        ROUTE,
        json=_get_request_payload_1(
            entity_id=morphology_id_public_inaccessible, labels=measurement_labels
        ),
    )
    assert_response(response, expected_status_code=404)

    response = client_user_1.get(ROUTE)
    assert_response(response, expected_status_code=200)
    assert len(response.json()["data"]) == 1

    # only return public results
    response = client_no_project.get(ROUTE)
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == measurement_annotation_id_public
