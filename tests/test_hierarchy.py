from functools import partial

import pytest

from app.db.model import Circuit, Derivation
from app.db.types import CircuitBuildCategory, CircuitScale, DerivationType

from tests.utils import PROJECT_ID, UNRELATED_PROJECT_ID, add_all_db, add_db, assert_request

ROUTE = "/circuit/hierarchy"


@pytest.fixture
def root_circuits(db, root_circuit_json_data, person_id):
    overrides = [
        {
            "authorized_project_id": PROJECT_ID,
            "authorized_public": True,
        },
        {
            "authorized_project_id": UNRELATED_PROJECT_ID,
            "authorized_public": True,
        },
        {
            "authorized_project_id": UNRELATED_PROJECT_ID,
            "authorized_public": False,
        },
    ]
    rows = [
        Circuit(
            **root_circuit_json_data
            | {
                "name": f"root-circuit-{i}",
                "created_by_id": person_id,
                "updated_by_id": person_id,
            }
            | override_dict
        )
        for i, override_dict in enumerate(overrides)
    ]
    return add_all_db(db, rows)


@pytest.fixture
def models(db, circuit_json_data, person_id, root_circuits):
    overrides = [
        {
            "scale": CircuitScale.single,
            "build_category": CircuitBuildCategory.computational_model,
            "authorized_project_id": PROJECT_ID,
            "authorized_public": False,
            "root_circuit_id": root_circuits[0].id,
        },
        {
            "scale": CircuitScale.microcircuit,
            "build_category": CircuitBuildCategory.em_reconstruction,
            "authorized_project_id": PROJECT_ID,
            "authorized_public": False,
            "root_circuit_id": root_circuits[0].id,
        },
        {
            "scale": CircuitScale.whole_brain,
            "build_category": CircuitBuildCategory.computational_model,
            "authorized_project_id": PROJECT_ID,
            "authorized_public": False,
            "root_circuit_id": root_circuits[0].id,
        },
        {
            "scale": CircuitScale.single,
            "build_category": CircuitBuildCategory.em_reconstruction,
            "authorized_project_id": PROJECT_ID,
            "authorized_public": False,
            "root_circuit_id": root_circuits[0].id,
        },
        {
            "scale": CircuitScale.microcircuit,
            "build_category": CircuitBuildCategory.computational_model,
            "authorized_project_id": PROJECT_ID,
            "authorized_public": False,
            "root_circuit_id": root_circuits[0].id,
        },
        {
            "scale": CircuitScale.whole_brain,
            "build_category": CircuitBuildCategory.em_reconstruction,
            "authorized_project_id": PROJECT_ID,
            "authorized_public": True,
            "root_circuit_id": root_circuits[1].id,
        },
        {
            "scale": CircuitScale.single,
            "build_category": CircuitBuildCategory.computational_model,
            "authorized_project_id": UNRELATED_PROJECT_ID,
            "authorized_public": False,
            "root_circuit_id": root_circuits[1].id,
        },
        {
            "scale": CircuitScale.microcircuit,
            "build_category": CircuitBuildCategory.em_reconstruction,
            "authorized_project_id": UNRELATED_PROJECT_ID,
            "authorized_public": False,
            "root_circuit_id": root_circuits[2].id,
        },
        {
            "scale": CircuitScale.microcircuit,
            "build_category": CircuitBuildCategory.em_reconstruction,
            "authorized_project_id": UNRELATED_PROJECT_ID,
            "authorized_public": True,
            "root_circuit_id": None,  # it's forbidden to link a private root_circuit_id
        },
    ]
    rows = [
        Circuit(
            **(
                circuit_json_data
                | {
                    "name": f"circuit-{i}",
                    "description": f"circuit-description-{i}",
                    "has_morphologies": i % 2 == 0,
                    "has_point_neurons": i % 2 == 0,
                    "has_electrical_cell_models": i % 2 == 0,
                    "has_spines": i % 2 == 0,
                    "number_neurons": 10 * i + 1,
                    "number_synapses": 1000 * i + 1,
                    "number_connections": 100 * i + 1,
                    "created_by_id": person_id,
                    "updated_by_id": person_id,
                }
                | override_dict
            )
        )
        for i, override_dict in enumerate(overrides)
    ]
    return add_all_db(db, rows)


@pytest.fixture
def hierarchy(db, root_circuits, models):
    """Build a circuit hierarchy.

    Mermaid diagram:

    ```mermaid
    flowchart TD
        R[R-u1-public]
        R0[R0-u1-public]
        R1[R1-u2-public]
        R2[R2-u2-private]

        C0[C0-u1-private]
        C1[C1-u1-private]
        C2[C2-u1-private]
        C3[C3-u1-private]
        C4[C4-u1-private]
        C5[C5-u1-public]
        C6[C6-u2-private]
        C7[C7-u2-private]

        C8[C8-u2-public]

        R0 -->|D0| C0
        C0 -->|D0| C1
        C0 -->|D1| C2
        R0 -->|D1| C3
        C3 -->|D0| C4

        R1 -->|D0| C5
        C5 -->|D0| C6

        R2 -->|D1| C7
        R2 -->|D0| C8

        C0 -->|D1| C4
    ```
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
        d0(used_id=r[2].id, generated_id=c[8].id),
        d1(used_id=c[0].id, generated_id=c[4].id),  # add multiple parents for c4
    ]
    return add_all_db(db, derivations)


@pytest.mark.usefixtures("hierarchy")
def test_hierarchy(db, client_user_1, client_user_2, root_circuit, root_circuits, models):
    # test with user_1, derivation_type=circuit_extraction
    response = assert_request(
        client_user_1.get, url=ROUTE, params={"derivation_type": DerivationType.circuit_extraction}
    ).json()
    assert response == {
        "derivation_type": "circuit_extraction",
        "data": [
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": False,
                "children": [],
                "id": str(models[2].id),
                "name": "circuit-2",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": False,
                "children": [
                    {
                        "authorized_project_id": str(PROJECT_ID),
                        "authorized_public": False,
                        "children": [],
                        "id": str(models[4].id),
                        "name": "circuit-4",
                        "parent_id": str(models[3].id),
                    },
                ],
                "id": str(models[3].id),
                "name": "circuit-3",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(UNRELATED_PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(models[8].id),
                "name": "circuit-8",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(root_circuit.id),
                "name": "root-circuit",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": True,
                "children": [
                    {
                        "authorized_project_id": str(PROJECT_ID),
                        "authorized_public": False,
                        "children": [
                            {
                                "authorized_project_id": str(PROJECT_ID),
                                "authorized_public": False,
                                "children": [],
                                "id": str(models[1].id),
                                "name": "circuit-1",
                                "parent_id": str(models[0].id),
                            },
                        ],
                        "id": str(models[0].id),
                        "name": "circuit-0",
                        "parent_id": str(root_circuits[0].id),
                    },
                ],
                "id": str(root_circuits[0].id),
                "name": "root-circuit-0",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(UNRELATED_PROJECT_ID),
                "authorized_public": True,
                "children": [
                    {
                        "authorized_project_id": str(PROJECT_ID),
                        "authorized_public": True,
                        "children": [],
                        "id": str(models[5].id),
                        "name": "circuit-5",
                        "parent_id": str(root_circuits[1].id),
                    },
                ],
                "id": str(root_circuits[1].id),
                "name": "root-circuit-1",
                "parent_id": None,
            },
        ],
    }

    # test with user_1, derivation_type=circuit_rewiring
    response = assert_request(
        client_user_1.get, url=ROUTE, params={"derivation_type": DerivationType.circuit_rewiring}
    ).json()
    assert response == {
        "derivation_type": "circuit_rewiring",
        "data": [
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": False,
                "children": [
                    {
                        "authorized_project_id": str(PROJECT_ID),
                        "authorized_public": False,
                        "children": [],
                        "id": str(models[2].id),
                        "name": "circuit-2",
                        "parent_id": str(models[0].id),
                    },
                    {
                        "authorized_project_id": str(PROJECT_ID),
                        "authorized_public": False,
                        "children": [],
                        "id": str(models[4].id),
                        "name": "circuit-4",
                        "parent_id": str(models[0].id),
                    },
                ],
                "id": str(models[0].id),
                "name": "circuit-0",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": False,
                "children": [],
                "id": str(models[1].id),
                "name": "circuit-1",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(models[5].id),
                "name": "circuit-5",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(UNRELATED_PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(models[8].id),
                "name": "circuit-8",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(root_circuit.id),
                "name": "root-circuit",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": True,
                "children": [
                    {
                        "authorized_project_id": str(PROJECT_ID),
                        "authorized_public": False,
                        "children": [],
                        "id": str(models[3].id),
                        "name": "circuit-3",
                        "parent_id": str(root_circuits[0].id),
                    },
                ],
                "id": str(root_circuits[0].id),
                "name": "root-circuit-0",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(UNRELATED_PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(root_circuits[1].id),
                "name": "root-circuit-1",
                "parent_id": None,
            },
        ],
    }

    # test with user_2, derivation_type=circuit_extraction
    response = assert_request(
        client_user_2.get, url=ROUTE, params={"derivation_type": DerivationType.circuit_extraction}
    ).json()
    assert response == {
        "derivation_type": "circuit_extraction",
        "data": [
            {
                "authorized_project_id": str(UNRELATED_PROJECT_ID),
                "authorized_public": False,
                "children": [],
                "id": str(models[7].id),
                "name": "circuit-7",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(root_circuit.id),
                "name": "root-circuit",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(root_circuits[0].id),
                "name": "root-circuit-0",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(UNRELATED_PROJECT_ID),
                "authorized_public": True,
                "children": [
                    {
                        "authorized_project_id": str(PROJECT_ID),
                        "authorized_public": True,
                        "children": [
                            {
                                "authorized_project_id": str(UNRELATED_PROJECT_ID),
                                "authorized_public": False,
                                "children": [],
                                "id": str(models[6].id),
                                "name": "circuit-6",
                                "parent_id": str(models[5].id),
                            },
                        ],
                        "id": str(models[5].id),
                        "name": "circuit-5",
                        "parent_id": str(root_circuits[1].id),
                    },
                ],
                "id": str(root_circuits[1].id),
                "name": "root-circuit-1",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(UNRELATED_PROJECT_ID),
                "authorized_public": False,
                "children": [
                    {
                        "authorized_project_id": str(UNRELATED_PROJECT_ID),
                        "authorized_public": True,
                        "children": [],
                        "id": str(models[8].id),
                        "name": "circuit-8",
                        "parent_id": str(root_circuits[2].id),
                    },
                ],
                "id": str(root_circuits[2].id),
                "name": "root-circuit-2",
                "parent_id": None,
            },
        ],
    }

    # test with user_2, derivation_type=circuit_rewiring
    response = assert_request(
        client_user_2.get, url=ROUTE, params={"derivation_type": DerivationType.circuit_rewiring}
    ).json()
    assert response == {
        "derivation_type": "circuit_rewiring",
        "data": [
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(models[5].id),
                "name": "circuit-5",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(UNRELATED_PROJECT_ID),
                "authorized_public": False,
                "children": [],
                "id": str(models[6].id),
                "name": "circuit-6",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(UNRELATED_PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(models[8].id),
                "name": "circuit-8",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(root_circuit.id),
                "name": "root-circuit",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(root_circuits[0].id),
                "name": "root-circuit-0",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(UNRELATED_PROJECT_ID),
                "authorized_public": True,
                "children": [],
                "id": str(root_circuits[1].id),
                "name": "root-circuit-1",
                "parent_id": None,
            },
            {
                "authorized_project_id": str(UNRELATED_PROJECT_ID),
                "authorized_public": False,
                "children": [
                    {
                        "authorized_project_id": str(UNRELATED_PROJECT_ID),
                        "authorized_public": False,
                        "children": [],
                        "id": str(models[7].id),
                        "name": "circuit-7",
                        "parent_id": str(root_circuits[2].id),
                    },
                ],
                "id": str(root_circuits[2].id),
                "name": "root-circuit-2",
                "parent_id": None,
            },
        ],
    }

    # add a wrong derivation, so that a circuit has multiple parents of the same derivation type
    add_db(
        db,
        Derivation(
            used_id=models[1].id,
            generated_id=models[4].id,
            derivation_type=DerivationType.circuit_rewiring,
        ),
    )
    response = assert_request(
        client_user_1.get,
        url=ROUTE,
        params={"derivation_type": DerivationType.circuit_rewiring},
        expected_status_code=500,
    ).json()
    assert response["details"] == "Inconsistent hierarchy."
