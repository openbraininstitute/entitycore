from app.db.model import Derivation

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
        for i in range(2)
    ]
    derivations = [
        Derivation(used_id=ecr_id, generated_id=generated_emodel_id) for ecr_id in trace_ids
    ]
    add_all_db(db, derivations)

    response = client.get(url=f"/emodel/{generated_emodel_id}/derived-from")

    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 2
    assert [data[0]["id"], data[1]["id"]] == [str(id_) for id_ in reversed(trace_ids)]
    assert all(d["type"] == "electrical_cell_recording" for d in data)

    response = client.get(url=f"/emodel/{other_emodel_id}/derived-from")

    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 0


def test_create_one(client, client_user_2, root_circuit, circuit):
    data = assert_request(
        client.post,
        url="/derivation",
        json={
            "used_id": str(root_circuit.id),
            "generated_id": str(circuit.id),
            "derivation_type": "circuit_extraction",
        },
    ).json()
    assert data == {
        "used": {"type": "circuit", "id": str(root_circuit.id)},
        "generated": {"type": "circuit", "id": str(circuit.id)},
        "derivation_type": "circuit_extraction",
    }

    data = assert_request(
        client_user_2.post,
        url="/derivation",
        json={
            "used_id": str(root_circuit.id),
            "generated_id": str(circuit.id),
            "derivation_type": "circuit_extraction",
        },
        expected_status_code=404,
    ).json()
    assert data["error_code"] == "ENTITY_NOT_FOUND"
