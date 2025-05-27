from app.db.model import Derivation

from tests.utils import add_all_db, assert_response, create_electrical_cell_recording_id


def test_get_electrical_cell_recording(
    db, client, create_emodel_ids, electrical_cell_recording_json_data
):
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
    assert {data[0]["id"], data[1]["id"]} == {str(id_) for id_ in trace_ids}
    assert all(d["type"] == "electrical_cell_recording" for d in data)

    response = client.get(url=f"/emodel/{other_emodel_id}/derived-from")

    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 0
