from functools import partial

import pytest

from app.db.model import Circuit, Derivation
from app.db.types import CircuitBuildCategory, CircuitScale, DerivationType

from tests.utils import PROJECT_ID, UNRELATED_PROJECT_ID, add_all_db, add_db, assert_request

ROUTE = "/circuit/hierarchy"


@pytest.fixture
def root_circuits(db, root_circuit_json_data, person_id):
    project_ids = [PROJECT_ID, UNRELATED_PROJECT_ID, UNRELATED_PROJECT_ID]
    public_values = [True, True, False]
    rows = [
        Circuit(
            **root_circuit_json_data
            | {
                "name": f"root-circuit-{i}",
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": project_id,
                "authorized_public": public,
            }
        )
        for i, (project_id, public) in enumerate(zip(project_ids, public_values, strict=True))
    ]
    return add_all_db(db, rows)


@pytest.fixture
def models(db, circuit_json_data, person_id, root_circuits):
    booleans = [True, False] * 4
    scales = (
        [
            CircuitScale.single,
            CircuitScale.microcircuit,
            CircuitScale.whole_brain,
        ]
        * 3
    )[:8]
    categories = [
        CircuitBuildCategory.computational_model,
        CircuitBuildCategory.em_reconstruction,
    ] * 4
    project_ids = [PROJECT_ID] * 6 + [UNRELATED_PROJECT_ID] * 2
    root_circuit_ids = [root_circuits[i].id for i in [0, 0, 0, 0, 0, 1, 1, 2]]
    rows = [
        Circuit(
            **(
                circuit_json_data
                | {
                    "name": f"circuit-{i}",
                    "description": f"circuit-description-{i}",
                    "has_morphologies": bool_value,
                    "has_point_neurons": bool_value,
                    "has_electrical_cell_models": bool_value,
                    "has_spines": bool_value,
                    "number_neurons": 10 * i + 1,
                    "number_synapses": 1000 * i + 1,
                    "number_connections": 100 * i + 1,
                    "scale": scale,
                    "build_category": category,
                    "created_by_id": person_id,
                    "updated_by_id": person_id,
                    "authorized_project_id": project_id,
                    "authorized_public": False,
                    "root_circuit_id": root_circuit_id,
                }
            )
        )
        for i, (bool_value, scale, category, project_id, root_circuit_id) in enumerate(
            zip(booleans, scales, categories, project_ids, root_circuit_ids, strict=True)
        )
    ]
    return add_all_db(db, rows)


@pytest.fixture
def hierarchy(db, root_circuits, models):
    """Build a circuit hierarchy.

    flowchart TD
        R0 -->|D0| C0
        C0 -->|D0| C1
        C0 -->|D1| C2
        R0 -->|D1| C3
        C3 -->|D0| C4

        R1 -->|D0| C5
        C5 -->|D0| C6

        R2 -->|D1| C7

        R
    """
    r = root_circuits
    c = models
    d0 = partial(Derivation, derivation_type=DerivationType.circuit_extraction)
    d1 = partial(Derivation, derivation_type=DerivationType.circuit_rewiring)
    derivations = [
        d0(used_id=r[0].id, generated_id=c[0].id),
        d0(used_id=c[0].id, generated_id=c[1].id),
        d1(used_id=c[0].id, generated_id=c[2].id),
        d1(used_id=r[0].id, generated_id=c[3].id),
        d0(used_id=c[3].id, generated_id=c[4].id),
        d0(used_id=r[1].id, generated_id=c[5].id),
        d0(used_id=c[5].id, generated_id=c[6].id),
        d1(used_id=r[2].id, generated_id=c[7].id),
    ]
    return add_all_db(db, derivations)


@pytest.mark.usefixtures("hierarchy")
def test_hierarchy(db, client_user_1, client_user_2, root_circuit, root_circuits, models):
    response = assert_request(client_user_1.get, url=ROUTE).json()
    assert response == {
        "data": [
            {
                "children": [],
                "derivation_type": None,
                "id": str(root_circuit.id),
                "name": "root-circuit",
                "parent_id": None,
            },
            {
                "children": [
                    {
                        "children": [
                            {
                                "children": [],
                                "derivation_type": "circuit_extraction",
                                "id": str(models[1].id),
                                "name": "circuit-1",
                                "parent_id": str(models[0].id),
                            },
                            {
                                "children": [],
                                "derivation_type": "circuit_rewiring",
                                "id": str(models[2].id),
                                "name": "circuit-2",
                                "parent_id": str(models[0].id),
                            },
                        ],
                        "derivation_type": "circuit_extraction",
                        "id": str(models[0].id),
                        "name": "circuit-0",
                        "parent_id": str(root_circuits[0].id),
                    },
                    {
                        "children": [
                            {
                                "children": [],
                                "derivation_type": "circuit_extraction",
                                "id": str(models[4].id),
                                "name": "circuit-4",
                                "parent_id": str(models[3].id),
                            },
                        ],
                        "derivation_type": "circuit_rewiring",
                        "id": str(models[3].id),
                        "name": "circuit-3",
                        "parent_id": str(root_circuits[0].id),
                    },
                ],
                "derivation_type": None,
                "id": str(root_circuits[0].id),
                "name": "root-circuit-0",
                "parent_id": None,
            },
            {
                "children": [
                    {
                        "children": [],
                        "derivation_type": "circuit_extraction",
                        "id": str(models[5].id),
                        "name": "circuit-5",
                        "parent_id": str(root_circuits[1].id),
                    },
                ],
                "derivation_type": None,
                "id": str(root_circuits[1].id),
                "name": "root-circuit-1",
                "parent_id": None,
            },
        ],
    }

    response = assert_request(client_user_2.get, url=ROUTE).json()
    assert response == {
        "data": [
            {
                "children": [],
                "derivation_type": None,
                "id": str(root_circuits[0].id),
                "name": "root-circuit-0",
                "parent_id": None,
            },
            {
                "children": [],
                "derivation_type": None,
                "id": str(root_circuits[1].id),
                "name": "root-circuit-1",
                "parent_id": None,
            },
            {
                "children": [
                    {
                        "children": [],
                        "derivation_type": "circuit_rewiring",
                        "id": str(models[7].id),
                        "name": "circuit-7",
                        "parent_id": str(root_circuits[2].id),
                    },
                ],
                "derivation_type": None,
                "id": str(root_circuits[2].id),
                "name": "root-circuit-2",
                "parent_id": None,
            },
        ],
    }

    # add a wrong derivation, so that a circuit has multiple parents
    add_db(
        db,
        Derivation(
            used_id=models[0].id,
            generated_id=models[4].id,
            derivation_type=DerivationType.circuit_rewiring,
        ),
    )
    response = assert_request(client_user_1.get, url=ROUTE, expected_status_code=500).json()
    assert response["details"] == "Inconsistent hierarchy."
