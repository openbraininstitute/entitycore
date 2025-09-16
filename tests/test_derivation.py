import pytest

from app.db.model import Derivation
from app.errors import ApiErrorCode
from app.schemas.api import ErrorResponse

from tests.utils import (
    add_all_db,
    assert_request,
    assert_response,
    create_electrical_cell_recording_id,
)


def test_get_derived_from(db, client, create_emodel_ids, electrical_cell_recording_json_data):
    # create two emodels, one with derivations and one without
    generated_emodel_id, other_emodel_id = create_emodel_ids(2)
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
                generated_id=generated_emodel_id,
                derivation_type="circuit_extraction",
            )
            for ecr_id in trace_ids[:3]
        ]
        + [
            Derivation(
                used_id=ecr_id, generated_id=generated_emodel_id, derivation_type="circuit_rewiring"
            )
            for ecr_id in trace_ids[3:5]
        ]
        + [
            Derivation(
                used_id=trace_ids[5],
                generated_id=generated_emodel_id,
                derivation_type="unspecified",
            )
        ]
    )
    add_all_db(db, derivations)

    response = client.get(
        url=f"/emodel/{generated_emodel_id}/derived-from",
        params={"derivation_type": "circuit_extraction"},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 3
    assert [d["id"] for d in data] == [str(id_) for id_ in reversed(trace_ids[:3])]
    assert all(d["type"] == "electrical_cell_recording" for d in data)

    response = client.get(
        url=f"/emodel/{generated_emodel_id}/derived-from",
        params={"derivation_type": "circuit_rewiring"},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 2
    assert [d["id"] for d in data] == [str(id_) for id_ in reversed(trace_ids[3:5])]
    assert all(d["type"] == "electrical_cell_recording" for d in data)

    response = client.get(
        url=f"/emodel/{generated_emodel_id}/derived-from", params={"derivation_type": "unspecified"}
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == str(trace_ids[5])
    assert data[0]["type"] == "electrical_cell_recording"

    # TODO: Change this test to invalid reqeust when derivation_type parameter set to not optional
    response = client.get(url=f"/emodel/{generated_emodel_id}/derived-from")
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 6

    # Test error invalid derivation_type param
    response = client.get(
        url=f"/emodel/{generated_emodel_id}/derived-from",
        params={"derivation_type": "invalid_type"},
    )
    assert_response(response, 422)
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST

    response = client.get(
        url=f"/emodel/{other_emodel_id}/derived-from", params={"derivation_type": "unspecified"}
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 0


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


@pytest.mark.parametrize(
    ("client_fixture", "expected_status", "expected_error"),
    [
        ("client_user_2", 404, "ENTITY_NOT_FOUND"),
        ("client_no_project", 403, "NOT_AUTHORIZED"),
    ],
)
def test_create_non_authorized(
    request, client_fixture, expected_status, expected_error, root_circuit, circuit
):
    client = request.getfixturevalue(client_fixture)

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
