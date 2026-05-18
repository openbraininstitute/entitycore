import uuid
from types import SimpleNamespace
from unittest.mock import ANY

import pytest

from app.config import settings
from app.db.model import Derivation
from app.db.types import DerivationType
from app.errors import ApiErrorCode
from app.filters.derivation import DerivationFilter
from app.queries.utils import is_user_authorized_for_deletion
from app.schemas.api import ErrorResponse

from tests.utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    PROJECT_ID,
    UNRELATED_PROJECT_ID,
    add_all_db,
    add_db,
    assert_request,
    assert_response,
    check_creation_fields,
    check_sort_by_field,
    create_electrical_cell_recording_id,
    create_person,
)

ROUTE = "/derivation"
ADMIN_ROUTE = "/admin/derivation"


def _add_derivation(
    db,
    *,
    used_id,
    generated_id,
    person_id,
    derivation_type=DerivationType.circuit_extraction,
    label=None,
):
    return add_db(
        db,
        Derivation(
            used_id=used_id,
            generated_id=generated_id,
            derivation_type=derivation_type,
            label=label,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )


def test_get_derived_from(
    db, clients, emodel_id, public_emodel_id, electrical_cell_recording_json_data, person_id
):
    # create two emodels, one with derivations and one without
    trace_ids = [
        create_electrical_cell_recording_id(
            clients.user_1, json_data=electrical_cell_recording_json_data | {"name": f"name-{i}"}
        )
        for i in range(6)
    ]
    derivations = (
        [
            Derivation(
                used_id=ecr_id,
                generated_id=public_emodel_id,
                derivation_type=DerivationType.circuit_extraction,
                created_by_id=person_id,
                updated_by_id=person_id,
            )
            for ecr_id in trace_ids[:3]
        ]
        + [
            Derivation(
                used_id=ecr_id,
                generated_id=public_emodel_id,
                derivation_type=DerivationType.circuit_rewiring,
                created_by_id=person_id,
                updated_by_id=person_id,
            )
            for ecr_id in trace_ids[3:5]
        ]
        + [
            Derivation(
                used_id=trace_ids[5],
                generated_id=emodel_id,  # private
                derivation_type=DerivationType.unspecified,
                created_by_id=person_id,
                updated_by_id=person_id,
            )
        ]
    )
    add_all_db(db, derivations)

    response = clients.user_1.get(
        url=f"/emodel/{public_emodel_id}/derived-from",
        params={"derivation_type": DerivationType.circuit_extraction},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 3
    assert [d["id"] for d in data] == [str(id_) for id_ in reversed(trace_ids[:3])]
    assert all(d["type"] == "electrical_cell_recording" for d in data)

    response = clients.user_1.get(
        url=f"/emodel/{public_emodel_id}/derived-from",
        params={"derivation_type": DerivationType.circuit_rewiring},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 2
    assert [d["id"] for d in data] == [str(id_) for id_ in reversed(trace_ids[3:5])]
    assert all(d["type"] == "electrical_cell_recording" for d in data)

    response = clients.user_1.get(
        url=f"/emodel/{emodel_id}/derived-from",
        params={"derivation_type": DerivationType.unspecified},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == str(trace_ids[5])
    assert data[0]["type"] == "electrical_cell_recording"

    # Test error not derivation_type param
    response = clients.user_1.get(url=f"/emodel/{public_emodel_id}/derived-from")
    assert_response(response, 422)
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST

    # Test error invalid derivation_type param
    response = clients.user_1.get(
        url=f"/emodel/{public_emodel_id}/derived-from",
        params={"derivation_type": "invalid_type"},
    )
    assert_response(response, 422)
    error = ErrorResponse.model_validate(response.json())
    assert error.error_code == ApiErrorCode.INVALID_REQUEST

    # Test empty result
    response = clients.user_1.get(
        url=f"/emodel/{public_emodel_id}/derived-from",
        params={"derivation_type": "unspecified"},
    )
    assert_response(response, 200)
    data = response.json()["data"]
    assert len(data) == 0

    # Test private unreadable entity
    response = clients.user_2.get(
        url=f"/emodel/{emodel_id}/derived-from",
        params={"derivation_type": "unspecified"},
    )
    assert_response(response, 404)
    assert response.json()["error_code"] == "ENTITY_NOT_FOUND"

    # Test non existing entity
    response = clients.user_2.get(
        url="/emodel/00000000-0000-0000-0000-000000000000/derived-from",
        params={"derivation_type": "unspecified"},
    )
    assert_response(response, 404)
    assert response.json()["error_code"] == "ENTITY_NOT_FOUND"

    data = assert_request(
        clients.admin.get,
        url=f"/admin/emodel/{public_emodel_id}/derived-from",
        params={"derivation_type": DerivationType.circuit_extraction},
    ).json()["data"]
    assert len(data) == 3

    data = assert_request(
        clients.admin.get,
        url=f"/admin/emodel/{emodel_id}/derived-from",
        params={"derivation_type": "unspecified"},
    ).json()["data"]
    assert len(data) == 1


def test_derived_from_entity_filter(
    db, clients, public_emodel_id, electrical_cell_recording_json_data, person_id
):
    """``derived-from`` supports ``BasicEntityFilter`` (type + ordering on ``Entity``)."""
    trace_ids = [
        create_electrical_cell_recording_id(
            clients.user_1, json_data=electrical_cell_recording_json_data | {"name": f"name-{i}"}
        )
        for i in range(3)
    ]
    add_all_db(
        db,
        [
            Derivation(
                used_id=trace_ids[i],
                generated_id=public_emodel_id,
                derivation_type=DerivationType.circuit_extraction,
                created_by_id=person_id,
                updated_by_id=person_id,
            )
            for i in range(3)
        ],
    )

    data = assert_request(
        clients.user_1.get,
        url=f"/emodel/{public_emodel_id}/derived-from",
        params={
            "derivation_type": DerivationType.circuit_extraction,
            "type": "electrical_cell_recording",
        },
    ).json()["data"]
    assert {d["id"] for d in data} == {str(tid) for tid in trace_ids}
    assert all(d["type"] == "electrical_cell_recording" for d in data)

    data = assert_request(
        clients.user_1.get,
        url=f"/emodel/{public_emodel_id}/derived-from",
        params={
            "derivation_type": DerivationType.circuit_extraction,
            "order_by": "creation_date",
        },
    ).json()["data"]
    assert [d["id"] for d in data] == [str(tid) for tid in trace_ids]

    data = assert_request(
        clients.user_1.get,
        url=f"/emodel/{public_emodel_id}/derived-from",
        params={
            "derivation_type": DerivationType.circuit_extraction,
            "order_by": "-creation_date",
        },
    ).json()["data"]
    assert [d["id"] for d in data] == [str(tid) for tid in reversed(trace_ids)]


def test_read_one(db, client, root_circuit, circuit, person_id):
    derivation = _add_derivation(
        db,
        used_id=root_circuit.id,
        generated_id=circuit.id,
        person_id=person_id,
    )

    data = assert_request(client.get, url=f"{ROUTE}/{derivation.id}").json()
    assert data["id"] == str(derivation.id)
    assert data["used"] == {"id": str(root_circuit.id), "type": "circuit"}
    assert data["generated"] == {"id": str(circuit.id), "type": "circuit"}
    assert data["derivation_type"] == DerivationType.circuit_extraction
    assert data["label"] is None
    check_creation_fields(data)


def test_missing(client, clients):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422

    assert_request(
        client.patch,
        url=f"{ROUTE}/{MISSING_ID}",
        json={"label": "nope"},
        expected_status_code=404,
    )
    assert_request(client.delete, url=f"{ROUTE}/{MISSING_ID}", expected_status_code=404)

    assert_request(clients.admin.get, url=f"{ADMIN_ROUTE}/{MISSING_ID}", expected_status_code=404)
    assert_request(
        clients.admin.patch,
        url=f"{ADMIN_ROUTE}/{MISSING_ID}",
        json={"label": "nope"},
        expected_status_code=404,
    )
    assert_request(
        clients.admin.delete, url=f"{ADMIN_ROUTE}/{MISSING_ID}", expected_status_code=404
    )


def test_read_one_authorization(db, clients, root_circuit, circuit, person_id):
    """Both `used` and `generated` must be readable by the caller."""
    derivation = _add_derivation(
        db,
        used_id=root_circuit.id,
        generated_id=circuit.id,
        person_id=person_id,
    )

    # user_1 owns PROJECT_ID, can read `circuit` (private) and `root_circuit` (public)
    assert_request(clients.user_1.get, url=f"{ROUTE}/{derivation.id}")

    # user_2 cannot read `circuit` (private to PROJECT_ID) -> 404
    response = clients.user_2.get(f"{ROUTE}/{derivation.id}")
    assert_response(response, 404)

    # admin on user route: no project context -> 404
    response = clients.admin.get(f"{ROUTE}/{derivation.id}")
    assert_response(response, 404)

    # admin via admin route can always read
    data = assert_request(clients.admin.get, url=f"{ADMIN_ROUTE}/{derivation.id}").json()
    assert data["id"] == str(derivation.id)


def test_read_many(db, clients, root_circuit_json_data, person_id):
    """A derivation is visible only if both used and generated are readable."""
    public_u1, private_u1, public_u2, private_u2 = _create_entities(
        "/circuit", clients.user_1, clients.user_2, json_data=root_circuit_json_data
    )

    d_pu_pr1 = _add_derivation(
        db, used_id=public_u1["id"], generated_id=private_u1["id"], person_id=person_id
    )
    d_pu_pu = _add_derivation(
        db, used_id=public_u1["id"], generated_id=public_u2["id"], person_id=person_id
    )
    d_pu_pr2 = _add_derivation(
        db, used_id=public_u2["id"], generated_id=private_u2["id"], person_id=person_id
    )
    d_pr_pr = _add_derivation(
        db, used_id=private_u2["id"], generated_id=private_u1["id"], person_id=person_id
    )

    # user_1 reads PROJECT_ID + public:
    # d_pu_pr1 (public+own_private), d_pu_pu (public+public) -> visible
    # d_pu_pr2 (public+other_private), d_pr_pr (other_private+own_private) -> hidden
    data = assert_request(clients.user_1.get, url=ROUTE).json()["data"]
    assert {d["id"] for d in data} == {str(d_pu_pr1.id), str(d_pu_pu.id)}

    # user_2 reads UNRELATED_PROJECT_ID + public:
    # d_pu_pu, d_pu_pr2 visible
    data = assert_request(clients.user_2.get, url=ROUTE).json()["data"]
    assert {d["id"] for d in data} == {str(d_pu_pu.id), str(d_pu_pr2.id)}

    # admin (no project) reads only fully-public derivations
    data = assert_request(clients.admin.get, url=ROUTE).json()["data"]
    assert {d["id"] for d in data} == {str(d_pu_pu.id)}

    # admin via admin route sees everything
    data = assert_request(clients.admin.get, url=ADMIN_ROUTE).json()["data"]
    assert {d["id"] for d in data} == {
        str(d_pu_pr1.id),
        str(d_pu_pu.id),
        str(d_pu_pr2.id),
        str(d_pr_pr.id),
    }


@pytest.fixture
def derivation_filter_models(db, root_circuit, circuit, public_circuit, person_id):
    """Build a small but varied set of derivations to drive filter/order tests.

    Two creators ("alice" / "bob"), three entities, six derivations that span every
    ``derivation_type`` used as an ordering value, mixed ``label`` (incl. NULLs) and
    every (used, generated) combination needed by ``used__id`` / ``generated__id``.
    Rows are committed one by one so that ``creation_date`` is strictly increasing.
    """
    alice = create_person(
        db,
        pref_label="alice",
        given_name="Alice",
        family_name="Anderson",
        sub_id=str(uuid.uuid4()),
        created_by_id=person_id,
    )
    bob = create_person(
        db,
        pref_label="bob",
        given_name="Bob",
        family_name="Brown",
        sub_id=str(uuid.uuid4()),
        created_by_id=person_id,
    )

    specs = [
        # (used, generated, derivation_type, label, creator)
        (root_circuit, circuit, DerivationType.circuit_extraction, None, alice),
        (root_circuit, public_circuit, DerivationType.circuit_rewiring, "label-b", bob),
        (circuit, public_circuit, DerivationType.circuit_customization, "label-a", alice),
        (public_circuit, circuit, DerivationType.emodel_circuit, "label-c", bob),
        (public_circuit, root_circuit, DerivationType.unspecified, None, alice),
        (circuit, root_circuit, DerivationType.circuit_extraction, "label-c", bob),
    ]
    rows = [
        _add_derivation(
            db,
            used_id=used.id,
            generated_id=generated.id,
            person_id=creator.id,
            derivation_type=derivation_type,
            label=label,
        )
        for used, generated, derivation_type, label, creator in specs
    ]
    return {
        "rows": rows,
        "alice": alice,
        "bob": bob,
        "entities": {
            "root_circuit": root_circuit,
            "circuit": circuit,
            "public_circuit": public_circuit,
        },
    }


def test_filtering_ordering(client, derivation_filter_models):
    rows = derivation_filter_models["rows"]
    alice = derivation_filter_models["alice"]
    bob = derivation_filter_models["bob"]
    root_circuit = derivation_filter_models["entities"]["root_circuit"]
    circuit = derivation_filter_models["entities"]["circuit"]
    public_circuit = derivation_filter_models["entities"]["public_circuit"]
    n_total = len(rows)

    def req(params):
        return assert_request(client.get, url=ROUTE, params=params).json()["data"]

    # --- Ordering: every supported field, ascending and descending, preserves count.
    for field in DerivationFilter.Constants.ordering_model_fields:
        for prefix in ("+", "-"):
            data = req({"order_by": f"{prefix}{field}"})
            assert len(data) == n_total, f"order_by={prefix}{field}"

    # Spot-check actual order on totally-ordered fields (no NULLs).
    check_sort_by_field(req({"order_by": "creation_date"}), "creation_date")
    check_sort_by_field(req({"order_by": "-creation_date"}), "creation_date", how="descending")
    check_sort_by_field(req({"order_by": "derivation_type"}), "derivation_type")
    check_sort_by_field(req({"order_by": "-derivation_type"}), "derivation_type", how="descending")
    # Nested ordering on used/generated: flatten and check via the nested id.
    used_ids = [d["used"]["id"] for d in req({"order_by": "used__id"})]
    assert used_ids == sorted(used_ids)
    generated_ids = [d["generated"]["id"] for d in req({"order_by": "-generated__id"})]
    assert generated_ids == sorted(generated_ids, reverse=True)

    # --- Filtering: id / id__in.
    assert {d["id"] for d in req({"id": str(rows[0].id)})} == {str(rows[0].id)}
    assert {d["id"] for d in req({"id__in": [str(rows[0].id), str(rows[3].id)]})} == {
        str(rows[0].id),
        str(rows[3].id),
    }

    # --- Filtering: scalar fields on Derivation itself.
    data = req({"derivation_type": DerivationType.circuit_extraction.value})
    assert {d["id"] for d in data} == {str(rows[0].id), str(rows[5].id)}

    data = req({"label": "label-c"})
    assert {d["id"] for d in data} == {str(rows[3].id), str(rows[5].id)}

    # --- Filtering: nested `used` (NestedEntityFilter prefix).
    assert {d["id"] for d in req({"used__id": str(root_circuit.id)})} == {
        str(rows[0].id),
        str(rows[1].id),
    }
    assert len(req({"used__id__in": [str(circuit.id), str(public_circuit.id)]})) == 4
    assert len(req({"used__type": "circuit"})) == n_total

    # --- Filtering: nested `generated` (NestedEntityFilter prefix).
    assert {d["id"] for d in req({"generated__id": str(root_circuit.id)})} == {
        str(rows[4].id),
        str(rows[5].id),
    }
    assert len(req({"generated__id__in": [str(circuit.id), str(public_circuit.id)]})) == 4
    assert len(req({"generated__type": "circuit"})) == n_total

    # --- Filtering: nested `created_by` / `updated_by` (NestedPersonFilter prefix).
    assert len(req({"created_by__id": str(alice.id)})) == 3
    assert len(req({"created_by__id__in": [str(alice.id), str(bob.id)]})) == n_total
    assert len(req({"created_by__pref_label": "alice"})) == 3
    assert len(req({"created_by__pref_label__in": ["alice", "bob"]})) == n_total
    assert len(req({"created_by__pref_label__ilike": "%lic%"})) == 3
    assert len(req({"created_by__given_name": "Bob"})) == 3
    assert len(req({"created_by__given_name__ilike": "%ob%"})) == 3
    assert len(req({"created_by__family_name": "Anderson"})) == 3
    assert len(req({"created_by__family_name__ilike": "%der%"})) == 3
    assert len(req({"created_by__sub_id": str(alice.sub_id)})) == 3
    assert len(req({"created_by__sub_id__in": [str(alice.sub_id), str(bob.sub_id)]})) == n_total
    assert len(req({"created_by__type": "person"})) == n_total
    # `updated_by` mirrors `created_by` here (same agent per row).
    assert len(req({"updated_by__pref_label": "bob"})) == 3
    assert len(req({"updated_by__pref_label__ilike": "%b%"})) == 3

    # --- Filtering: creation/update date ranges (CreationFilterMixin).
    mid_date = rows[2].creation_date.isoformat()
    assert len(req({"creation_date__gte": mid_date})) == 4
    assert len(req({"creation_date__lte": mid_date})) == 3
    mid_update = rows[2].update_date.isoformat()
    assert len(req({"update_date__gte": mid_update})) == 4
    assert len(req({"update_date__lte": mid_update})) == 3

    # --- Combos.
    data = req(
        {
            "derivation_type": DerivationType.circuit_extraction.value,
            "created_by__pref_label": "alice",
        }
    )
    assert {d["id"] for d in data} == {str(rows[0].id)}

    data = req(
        {
            "used__id": str(root_circuit.id),
            "order_by": "-creation_date",
        }
    )
    assert [d["id"] for d in data] == [str(rows[1].id), str(rows[0].id)]


def test_update_one(db, clients, root_circuit, circuit, person_id):
    """Update authorization mirrors `update_one`'s `constrain_to_writable_entities` rule:

    only callers that can write to the derivation's ``generated`` entity may patch it.
    """
    derivation = _add_derivation(
        db,
        used_id=root_circuit.id,
        generated_id=circuit.id,
        person_id=person_id,
        derivation_type=DerivationType.circuit_extraction,
    )
    did = str(derivation.id)

    # user_2 cannot write to `circuit` (PROJECT_ID, private) -> 404
    data = assert_request(
        clients.user_2.patch,
        url=f"{ROUTE}/{did}",
        json={"derivation_type": DerivationType.unspecified.value},
        expected_status_code=404,
    ).json()
    assert data["error_code"] == "ENTITY_NOT_FOUND"

    # user_1 owns the generated entity -> update succeeds
    data = assert_request(
        clients.user_1.patch,
        url=f"{ROUTE}/{did}",
        json={"derivation_type": DerivationType.unspecified.value, "label": "label-u1"},
    ).json()
    assert data["derivation_type"] == DerivationType.unspecified
    assert data["label"] == "label-u1"
    assert data["updated_by"]["id"] == str(person_id)

    data = assert_request(clients.user_1.get, url=f"{ROUTE}/{did}").json()
    assert data["derivation_type"] == DerivationType.unspecified
    assert data["label"] == "label-u1"

    # admin on regular route: no project context -> 404
    data = assert_request(
        clients.admin.patch,
        url=f"{ROUTE}/{did}",
        json={"label": "label-should-not-stick"},
        expected_status_code=404,
    ).json()
    assert data["error_code"] == "ENTITY_NOT_FOUND"

    data = assert_request(clients.user_1.get, url=f"{ROUTE}/{did}").json()
    assert data["label"] == "label-u1"

    # admin on admin route bypasses writable-entity checks
    data = assert_request(
        clients.admin.patch,
        url=f"{ADMIN_ROUTE}/{did}",
        json={
            "label": "label-admin",
            "derivation_type": DerivationType.circuit_rewiring.value,
        },
    ).json()
    assert data["label"] == "label-admin"
    assert data["derivation_type"] == DerivationType.circuit_rewiring

    data = assert_request(clients.user_1.get, url=f"{ROUTE}/{did}").json()
    assert data["label"] == "label-admin"
    assert data["derivation_type"] == DerivationType.circuit_rewiring

    # patching with an unknown id -> 404 for both regular and admin routes
    assert_request(
        clients.user_1.patch,
        url=f"{ROUTE}/{MISSING_ID}",
        json={"label": "nope"},
        expected_status_code=404,
    )
    assert_request(
        clients.admin.patch,
        url=f"{ADMIN_ROUTE}/{MISSING_ID}",
        json={"label": "nope"},
        expected_status_code=404,
    )


@pytest.mark.parametrize(
    "derivation_type",
    [
        "circuit_customization",
        DerivationType.circuit_extraction,
        "circuit_rewiring",
        "emodel_circuit",
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
        "id": ANY,
        "used": {"type": "circuit", "id": str(root_circuit.id)},
        "generated": {"type": "circuit", "id": str(circuit.id)},
        "derivation_type": derivation_type,
        "label": None,
        "created_by": ANY,
        "updated_by": ANY,
        "creation_date": ANY,
        "update_date": ANY,
    }
    check_creation_fields(data)


def test_admin_read_many_filter(db, clients, root_circuit, circuit, person_id):
    """Admin list route sees derivations hidden from the user route and supports filters."""
    derivation = _add_derivation(
        db,
        used_id=root_circuit.id,
        generated_id=circuit.id,
        person_id=person_id,
    )

    assert_request(clients.user_1.get, url=f"{ROUTE}/{derivation.id}")

    data = assert_request(
        clients.admin.get,
        url=ADMIN_ROUTE,
        params={"id": str(derivation.id)},
    ).json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == str(derivation.id)

    data = assert_request(
        clients.admin.get,
        url=ADMIN_ROUTE,
        params={"derivation_type": DerivationType.circuit_extraction.value},
    ).json()["data"]
    assert {d["id"] for d in data} == {str(derivation.id)}


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
    assert data["used"] == {"type": "emodel", "id": str(emodel_id)}
    assert data["generated"] == {"type": "circuit", "id": str(circuit.id)}
    assert data["derivation_type"] == str(DerivationType.emodel_circuit)
    assert data["label"] == "hoc:cADpyr_L5TPC"


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
    assert data["used"] == {"type": "circuit", "id": str(root_circuit.id)}
    assert data["generated"] == {"type": "circuit", "id": str(circuit.id)}
    assert data["derivation_type"] == str(DerivationType.circuit_customization)
    assert data["label"] == "synaptic_modification"


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
            "derivation_type": DerivationType.circuit_extraction,
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
                "derivation_type": DerivationType.circuit_extraction,
            },
            expected_status_code=expected_status,
            context=f"Test {i}",
        ).json()
        if expected_status == 200:
            assert data["generated"]["id"] == generated_id, f"Error in test {i}"
            assert data["used"]["id"] == used_id, f"Error in test {i}"
        elif expected_status == 404:
            assert data["error_code"] == "ENTITY_NOT_FOUND", f"Error in test {i}"


def _post_derivation(client, *, used_id, generated_id):
    return assert_request(
        client.post,
        url=ROUTE,
        json={
            "used_id": str(used_id),
            "generated_id": str(generated_id),
            "derivation_type": DerivationType.circuit_extraction.value,
        },
    ).json()


def test_user_delete_one(clients, root_circuit, circuit, public_circuit, circuit_json_data):
    """``delete_one`` delegates to ``is_user_authorized_for_deletion`` on the generated entity."""

    # Private generated entity in PROJECT_ID (created by ``person_id`` / user_1's project).
    data = _post_derivation(clients.user_1, used_id=root_circuit.id, generated_id=circuit.id)
    did = data["id"]

    # Wrong project: derivation is found, but generated entity is not deletable -> 403.
    data = assert_request(
        clients.user_2.delete, url=f"{ROUTE}/{did}", expected_status_code=403
    ).json()
    assert data["error_code"] == "ENTITY_FORBIDDEN"

    # Same-project member who did not create the generated entity -> 403.
    data = assert_request(
        clients.user_3.delete, url=f"{ROUTE}/{did}", expected_status_code=403
    ).json()
    assert data["error_code"] == "ENTITY_FORBIDDEN"

    # Project admin may delete (private entity in their project).
    data = assert_request(clients.user_1.delete, url=f"{ROUTE}/{did}").json()
    assert data["id"] == did
    assert_request(clients.user_1.get, url=f"{ROUTE}/{did}", expected_status_code=404)

    # Public generated entities cannot be deleted by non-maintainers.
    data = _post_derivation(clients.user_1, used_id=root_circuit.id, generated_id=public_circuit.id)
    did_public = data["id"]
    data = assert_request(
        clients.user_1.delete, url=f"{ROUTE}/{did_public}", expected_status_code=403
    ).json()
    assert data["error_code"] == "ENTITY_FORBIDDEN"

    # Service maintainer in the project may delete public generated entities.
    data = assert_request(clients.maintainer_1.delete, url=f"{ROUTE}/{did_public}").json()
    assert data["id"] == did_public

    # Project member may delete when they created the generated entity.
    circuit_u3 = assert_request(
        clients.user_3.post,
        url="/circuit",
        json=circuit_json_data | {"name": "circuit-u3-delete"},
    ).json()
    data = _post_derivation(clients.user_3, used_id=root_circuit.id, generated_id=circuit_u3["id"])
    did_u3 = data["id"]
    data = assert_request(clients.user_3.delete, url=f"{ROUTE}/{did_u3}").json()
    assert data["id"] == did_u3

    # Unknown id -> 404.
    assert_request(clients.user_1.delete, url=f"{ROUTE}/{MISSING_ID}", expected_status_code=404)


def test_delete_auth_disabled(monkeypatch, clients, root_circuit, circuit):
    """When auth is disabled, any user may delete."""
    monkeypatch.setattr(settings, "APP_DISABLE_AUTH", True)
    data = _post_derivation(clients.user_1, used_id=root_circuit.id, generated_id=circuit.id)
    did = data["id"]
    data = assert_request(clients.user_2.delete, url=f"{ROUTE}/{did}").json()
    assert data["id"] == did


def test_is_user_authorized_for_deletion_without_project_id(db, user_context_user_1):
    obj = SimpleNamespace(authorized_public=False)
    assert is_user_authorized_for_deletion(db, user_context_user_1, obj) is False


def test_admin_delete_one(db, clients, client_admin, root_circuit, circuit, person_id):
    """Admin delete uses the generic admin service and does not apply ``delete_one`` auth."""
    derivation = _add_derivation(
        db,
        used_id=root_circuit.id,
        generated_id=circuit.id,
        person_id=person_id,
    )
    did = str(derivation.id)

    data = assert_request(
        clients.user_1.delete, url=f"{ADMIN_ROUTE}/{did}", expected_status_code=403
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ADMIN_ROUTE}/{did}").json()
    assert data["id"] == did

    assert_request(clients.user_1.get, url=f"{ROUTE}/{did}", expected_status_code=404)
