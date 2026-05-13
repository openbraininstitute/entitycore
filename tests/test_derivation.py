import pytest

from app.db.model import Circuit, Derivation
from app.errors import ApiErrorCode
from app.schemas.api import ErrorResponse

from tests.utils import (
    PROJECT_ID,
    UNRELATED_PROJECT_ID,
    add_all_db,
    add_db,
    assert_request,
    assert_response,
)


def _add_source_circuit(db, root_circuit_json_data, person_id, name):
    return add_db(
        db,
        Circuit(
            **root_circuit_json_data
            | {
                "name": name,
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
                "authorized_public": True,
            }
        ),
    )


def test_get_derived_from(
    db,
    clients,
    person_id,
    public_root_circuit,
    root_circuit,
    root_circuit_json_data,
):
    # Create source circuits (used) for the typed derivations.
    # Source/target circuits use circuit_extraction / circuit_rewiring
    # (circuit -> circuit), and a single unspecified derivation goes to a
    # private target. Direct DB inserts via add_all_db bypass the create-time
    # type validator, but the data still satisfies it for consistency.
    source_ids = [
        _add_source_circuit(db, root_circuit_json_data, person_id, f"source-{i}").id
        for i in range(6)
    ]
    derivations = (
        [
            Derivation(
                used_id=src_id,
                generated_id=public_root_circuit.id,
                derivation_type="circuit_extraction",
            )
            for src_id in source_ids[:3]
        ]
        + [
            Derivation(
                used_id=src_id,
                generated_id=public_root_circuit.id,
                derivation_type="circuit_rewiring",
            )
            for src_id in source_ids[3:5]
        ]
        + [
            Derivation(
                used_id=source_ids[5],
                generated_id=root_circuit.id,  # private
                derivation_type="unspecified",
            )
        ]
    )
    add_all_db(db, derivations)

    response = clients.user_1.get(
        url=f"/circuit/{public_root_circuit.id}/derived-from",
        params={"derivation_type": "circuit_extraction"},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 3
    assert [d["id"] for d in data] == [str(id_) for id_ in reversed(source_ids[:3])]
    assert all(d["type"] == "circuit" for d in data)

    response = clients.user_1.get(
        url=f"/circuit/{public_root_circuit.id}/derived-from",
        params={"derivation_type": "circuit_rewiring"},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 2
    assert [d["id"] for d in data] == [str(id_) for id_ in reversed(source_ids[3:5])]
    assert all(d["type"] == "circuit" for d in data)

    response = clients.user_1.get(
        url=f"/circuit/{root_circuit.id}/derived-from",
        params={"derivation_type": "unspecified"},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == str(source_ids[5])
    assert data[0]["type"] == "circuit"

    # Test error not derivation_type param
    response = clients.user_1.get(url=f"/circuit/{public_root_circuit.id}/derived-from")
    assert_response(response, 422)
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST

    # Test error invalid derivation_type param
    response = clients.user_1.get(
        url=f"/circuit/{public_root_circuit.id}/derived-from",
        params={"derivation_type": "invalid_type"},
    )
    assert_response(response, 422)
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST

    # Test empty result
    response = clients.user_1.get(
        url=f"/circuit/{public_root_circuit.id}/derived-from",
        params={"derivation_type": "unspecified"},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 0

    # Test private unreadable entity
    response = clients.user_2.get(
        url=f"/circuit/{root_circuit.id}/derived-from",
        params={"derivation_type": "unspecified"},
    )
    assert_response(response, 404)
    assert response.json()["error_code"] == "ENTITY_NOT_FOUND"

    # Test non existing entity
    response = clients.user_2.get(
        url="/circuit/00000000-0000-0000-0000-000000000000/derived-from",
        params={"derivation_type": "unspecified"},
    )
    assert_response(response, 404)
    assert response.json()["error_code"] == "ENTITY_NOT_FOUND"

    data = assert_request(
        clients.admin.get,
        url=f"/admin/circuit/{public_root_circuit.id}/derived-from",
        params={"derivation_type": "circuit_extraction"},
    ).json()["data"]
    assert len(data) == 3

    data = assert_request(
        clients.admin.get,
        url=f"/admin/circuit/{root_circuit.id}/derived-from",
        params={"derivation_type": "unspecified"},
    ).json()["data"]
    assert len(data) == 1


@pytest.mark.parametrize(
    "derivation_type",
    [
        "circuit_customization",
        "circuit_extraction",
        "circuit_rewiring",
        "unspecified",
    ],
)
def test_create_one(client, derivation_type, root_circuit, circuit):
    """Create derivations between two circuits (covered by validation rules).

    ``emodel_circuit`` is excluded here because it requires used=emodel,
    generated=circuit; it is exercised in ``test_create_emodel_circuit_with_label``.
    """
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
        "label": None,
    }


def test_create_emodel_circuit_with_label(client, emodel_id, circuit):
    """Link an emodel (used) to a circuit (generated) with the SONATA model_template label."""
    data = assert_request(
        client.post,
        url="/derivation",
        json={
            "used_id": str(emodel_id),
            "generated_id": str(circuit.id),
            "derivation_type": "emodel_circuit",
            "label": "hoc:cADpyr_L5TPC",
        },
    ).json()
    assert data == {
        "used": {"type": "emodel", "id": str(emodel_id)},
        "generated": {"type": "circuit", "id": str(circuit.id)},
        "derivation_type": "emodel_circuit",
        "label": "hoc:cADpyr_L5TPC",
    }


def test_create_circuit_customization_with_label(client, root_circuit, circuit):
    """Derive a circuit from another by customizing components, with a label for the type."""
    data = assert_request(
        client.post,
        url="/derivation",
        json={
            "used_id": str(root_circuit.id),
            "generated_id": str(circuit.id),
            "derivation_type": "circuit_customization",
            "label": "synaptic_modification",
        },
    ).json()
    assert data == {
        "used": {"type": "circuit", "id": str(root_circuit.id)},
        "generated": {"type": "circuit", "id": str(circuit.id)},
        "derivation_type": "circuit_customization",
        "label": "synaptic_modification",
    }


@pytest.mark.parametrize(
    ("derivation_type", "label"),
    [
        ("emodel_circuit", "cADpyr_L5TPC"),  # missing hoc: prefix
        ("emodel_circuit", "hoc:"),  # empty template name
        ("emodel_circuit", "nml:cADpyr_L5TPC"),  # wrong prefix
        ("circuit_customization", "unknown_modification"),
        ("circuit_customization", ""),
    ],
)
def test_create_invalid_label_for_derivation_type(
    client, emodel_id, circuit, derivation_type, label
):
    used_id = emodel_id if derivation_type == "emodel_circuit" else str(circuit.id)
    data = assert_request(
        client.post,
        url="/derivation",
        json={
            "used_id": str(used_id),
            "generated_id": str(circuit.id),
            "derivation_type": derivation_type,
            "label": label,
        },
        expected_status_code=422,
    ).json()
    assert data["error_code"] == "INVALID_REQUEST"


@pytest.mark.parametrize(
    ("derivation_type", "use_emodel_as_used", "use_emodel_as_generated"),
    [
        # circuit-only types reject emodel as the used entity
        ("circuit_extraction", True, False),
        ("circuit_rewiring", True, False),
        ("circuit_customization", True, False),
        # emodel_circuit rejects circuit as used
        ("emodel_circuit", False, False),
        # emodel_circuit rejects emodel as generated
        ("emodel_circuit", True, True),
    ],
)
def test_create_invalid_entity_types_for_derivation_type(
    client,
    emodel_id,
    public_emodel_id,
    root_circuit,
    circuit,
    derivation_type,
    use_emodel_as_used,
    use_emodel_as_generated,
):
    used_id = str(emodel_id) if use_emodel_as_used else str(root_circuit.id)
    generated_id = str(public_emodel_id) if use_emodel_as_generated else str(circuit.id)
    data = assert_request(
        client.post,
        url="/derivation",
        json={
            "used_id": used_id,
            "generated_id": generated_id,
            "derivation_type": derivation_type,
        },
        expected_status_code=422,
    ).json()
    assert data["error_code"] == "INVALID_REQUEST"


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


def test_user_delete_one(client, root_circuit, circuit):
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
