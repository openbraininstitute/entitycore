import pytest

from app.db.model import Derivation
from app.errors import ApiErrorCode
from app.schemas.api import ErrorResponse

from tests.utils import (
    PROJECT_ID,
    UNRELATED_PROJECT_ID,
    add_all_db,
    assert_request,
    assert_response,
    create_electrical_cell_recording_id,
)


def test_get_derived_from(
    db, client, client_user_2, emodel_id, public_emodel_id, electrical_cell_recording_json_data
):
    # create two emodels, one with derivations and one without
    trace_ids = [
        create_electrical_cell_recording_id(
            client, json_data=electrical_cell_recording_json_data | {"name": f"name-{i}"}
        )
        for i in range(6)
    ]
    derivations = (
        [
            Derivation(
                used_id=ecr_id,
                generated_id=public_emodel_id,
                derivation_type="circuit_extraction",
            )
            for ecr_id in trace_ids[:3]
        ]
        + [
            Derivation(
                used_id=ecr_id,
                generated_id=public_emodel_id,
                derivation_type="circuit_rewiring",
            )
            for ecr_id in trace_ids[3:5]
        ]
        + [
            Derivation(
                used_id=trace_ids[5],
                generated_id=emodel_id,  # private
                derivation_type="unspecified",
            )
        ]
    )
    add_all_db(db, derivations)

    response = client.get(
        url=f"/emodel/{public_emodel_id}/derived-from",
        params={"derivation_type": "circuit_extraction"},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 3
    assert [d["id"] for d in data] == [str(id_) for id_ in reversed(trace_ids[:3])]
    assert all(d["type"] == "electrical_cell_recording" for d in data)

    response = client.get(
        url=f"/emodel/{public_emodel_id}/derived-from",
        params={"derivation_type": "circuit_rewiring"},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 2
    assert [d["id"] for d in data] == [str(id_) for id_ in reversed(trace_ids[3:5])]
    assert all(d["type"] == "electrical_cell_recording" for d in data)

    response = client.get(
        url=f"/emodel/{emodel_id}/derived-from",
        params={"derivation_type": "unspecified"},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == str(trace_ids[5])
    assert data[0]["type"] == "electrical_cell_recording"

    # Test error not derivation_type param
    response = client.get(url=f"/emodel/{public_emodel_id}/derived-from")
    assert_response(response, 422)
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST

    # Test error invalid derivation_type param
    response = client.get(
        url=f"/emodel/{public_emodel_id}/derived-from",
        params={"derivation_type": "invalid_type"},
    )
    assert_response(response, 422)
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST

    # Test empty result
    response = client.get(
        url=f"/emodel/{public_emodel_id}/derived-from",
        params={"derivation_type": "unspecified"},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 0

    # Test private unreadable entity
    response = client_user_2.get(
        url=f"/emodel/{emodel_id}/derived-from",
        params={"derivation_type": "unspecified"},
    )
    assert_response(response, 404)
    assert response.json()["error_code"] == "ENTITY_NOT_FOUND"

    # Test non existing entity
    response = client_user_2.get(
        url="/emodel/00000000-0000-0000-0000-000000000000/derived-from",
        params={"derivation_type": "unspecified"},
    )
    assert_response(response, 404)
    assert response.json()["error_code"] == "ENTITY_NOT_FOUND"


@pytest.mark.parametrize(
    "derivation_type",
    [
        "circuit_extraction",
        "circuit_rewiring",
        "unspecified",
    ],
)
def test_create_one(client, derivation_type, root_circuit, circuit):
    data = assert_request(
        client.post,
        url="/derivation",
        json={
            "used_id": str(root_circuit.id),
            "generated_id": str(circuit.id),
            "derivation_type": derivation_type,
        },
    ).json()
    assert data == {
        "used": {"type": "circuit", "id": str(root_circuit.id)},
        "generated": {"type": "circuit", "id": str(circuit.id)},
        "derivation_type": derivation_type,
    }


def test_create_invalid_data(client, root_circuit, circuit):
    # test that the derivation type is mandatory
    data = assert_request(
        client.post,
        url="/derivation",
        json={
            "used_id": str(root_circuit.id),
            "generated_id": str(circuit.id),
        },
        expected_status_code=422,
    ).json()
    assert data["error_code"] == "INVALID_REQUEST"


def test_create_without_authorization(client_no_project, root_circuit, circuit):
    client = client_no_project
    expected_status = 403
    expected_error = "NOT_AUTHORIZED"

    data = assert_request(
        client.post,
        url="/derivation",
        json={
            "used_id": str(root_circuit.id),
            "generated_id": str(circuit.id),
            "derivation_type": "circuit_extraction",
        },
        expected_status_code=expected_status,
    ).json()
    assert data["error_code"] == expected_error


def _create_entities(route, client_user_1, client_user_2, json_data):
    """Create public and private entities.

    Created entities:

    public_u1 (PROJECT_ID)
    private_u1 (PROJECT_ID)
    public_u2 (UNRELATED_PROJECT_ID)
    private_u2 (UNRELATED_PROJECT_ID)
    """
    public_u1 = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"name": "Public u1/0", "authorized_public": True},
    ).json()
    assert public_u1["authorized_public"] is True
    assert public_u1["authorized_project_id"] == PROJECT_ID

    private_u1 = assert_request(
        client_user_1.post,
        url=route,
        json=json_data | {"name": "Private u1/0", "authorized_public": False},
    ).json()
    assert private_u1["authorized_public"] is False
    assert private_u1["authorized_project_id"] == PROJECT_ID

    public_u2 = assert_request(
        client_user_2.post,
        url=route,
        json=json_data | {"name": "Public u2/0", "authorized_public": True},
    ).json()
    assert public_u2["authorized_public"] is True
    assert public_u2["authorized_project_id"] == UNRELATED_PROJECT_ID

    private_u2 = assert_request(
        client_user_2.post,
        url=route,
        json=json_data | {"name": "Private u2/0", "authorized_public": False},
    ).json()
    assert private_u2["authorized_public"] is False
    assert private_u2["authorized_project_id"] == UNRELATED_PROJECT_ID

    return public_u1, private_u1, public_u2, private_u2


def test_create_with_authorization(client_user_1, client_user_2, root_circuit_json_data):
    """Check the authorization when trying to create the derivation."""
    route = "/circuit"
    public_u1, private_u1, public_u2, private_u2 = _create_entities(
        route, client_user_1, client_user_2, json_data=root_circuit_json_data
    )

    # these calls are done with client_user_1, that can create derivations for u1 entitites only
    for i, (used_id, generated_id, expected_status) in enumerate(
        [
            (public_u1["id"], public_u1["id"], 200),
            (private_u1["id"], public_u1["id"], 200),
            (public_u2["id"], public_u1["id"], 200),
            (private_u2["id"], public_u1["id"], 404),  # used_id cannot be read
            (public_u1["id"], private_u1["id"], 200),
            (private_u1["id"], private_u1["id"], 200),
            (public_u2["id"], private_u1["id"], 200),
            (private_u2["id"], private_u1["id"], 404),  # used_id cannot be read
            (public_u1["id"], public_u2["id"], 404),  # generated_id is in a different project
            (private_u1["id"], public_u2["id"], 404),  # generated_id is in a different project
            (public_u2["id"], public_u2["id"], 404),  # generated_id is in a different project
            (private_u2["id"], public_u2["id"], 404),  # generated_id is in a different project
            (public_u1["id"], private_u2["id"], 404),  # generated_id cannot be read
            (private_u1["id"], private_u2["id"], 404),  # generated_id cannot be read
            (public_u2["id"], private_u2["id"], 404),  # generated_id cannot be read
            (private_u2["id"], private_u2["id"], 404),  # generated_id cannot be read
        ]
    ):
        data = assert_request(
            client_user_1.post,
            url="/derivation",
            json={
                "used_id": used_id,
                "generated_id": generated_id,
                "derivation_type": "circuit_extraction",
            },
            expected_status_code=expected_status,
            context=f"Test {i}",
        ).json()
        if expected_status == 200:
            assert data["generated"]["id"] == generated_id, f"Error in test {i}"
            assert data["used"]["id"] == used_id, f"Error in test {i}"
        elif expected_status == 404:
            assert data["error_code"] == "ENTITY_NOT_FOUND", f"Error in test {i}"


def test_delete_one(client, root_circuit, circuit):
    data = assert_request(
        client.post,
        url="/derivation",
        json={
            "used_id": str(root_circuit.id),
            "generated_id": str(circuit.id),
            "derivation_type": "circuit_extraction",
        },
    ).json()
    data = assert_request(
        client.delete,
        url="/derivation",
        params={
            "used_id": str(root_circuit.id),
            "generated_id": str(circuit.id),
            "derivation_type": "circuit_extraction",
        },
    ).json()
    assert data["used"]["id"] == str(root_circuit.id)
    assert data["generated"]["id"] == str(circuit.id)
