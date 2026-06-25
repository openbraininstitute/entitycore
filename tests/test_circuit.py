import pytest

from app.db.model import (
    Circuit,
    Derivation,
    ExternalUrl,
    Publication,
    ScientificArtifactExternalUrlLink,
    ScientificArtifactPublicationLink,
)
from app.db.types import (
    CircuitBuildCategory,
    CircuitScale,
    DerivationType,
    EntityType,
    ExternalSource,
    PublicationType,
    TargetSimulator,
)

from .utils import (
    PROJECT_ID,
    add_all_db,
    add_db,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_deletion_cascades,
    check_entity_delete_one,
    check_entity_read_many,
    check_entity_update_one,
    check_missing,
    check_pagination,
)

ROUTE = "/circuit"
ADMIN_ROUTE = "/admin/circuit"


@pytest.fixture
def create_id(client, root_circuit_json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=root_circuit_json_data | kwargs).json()[
            "id"
        ]

    return _create_id


def _assert_read_response(data, json_data):
    assert "id" in data
    assert "authorized_public" in data
    assert "authorized_project_id" in data
    assert "assets" in data
    assert data["name"] == json_data["name"]
    assert data["description"] == json_data["description"]
    assert data["subject"]["id"] == json_data["subject_id"]
    assert data["license"]["id"] == json_data["license_id"]
    assert data["root_circuit_id"] == json_data["root_circuit_id"]
    assert data["atlas_id"] == json_data["atlas_id"]
    assert data["type"] == EntityType.circuit
    assert data["has_morphologies"] == json_data["has_morphologies"]
    assert data["has_point_neurons"] == json_data["has_point_neurons"]
    assert data["has_electrical_cell_models"] == json_data["has_electrical_cell_models"]
    assert data["has_spines"] == json_data["has_spines"]
    assert data["build_category"] == json_data["build_category"]
    assert data["scale"] == json_data["scale"]
    assert data["authorized_public"] is json_data["authorized_public"]
    assert data["target_simulator"] == TargetSimulator.neuron

    check_creation_fields(data)


def test_create_one(client, circuit_json_data):
    data = assert_request(client.post, url=ROUTE, json=circuit_json_data).json()
    _assert_read_response(data, circuit_json_data)


def test_update_one(clients, circuit_json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=circuit_json_data,
        patch_payload={
            "name": "name",
            "description": "description",
        },
        optional_payload={
            "number_connections": 750,
        },
    )


def test_read_one(client, client_admin, circuit, circuit_json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{circuit.id}").json()
    _assert_read_response(data, circuit_json_data)
    assert len(data["contributions"]) == 1

    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{circuit.id}").json()
    _assert_read_response(data, circuit_json_data)
    assert len(data["contributions"]) == 1


def test_read_many_2(clients, root_circuit_json_data):
    check_entity_read_many(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=root_circuit_json_data,
    )


def test_delete_one(db, clients, root_circuit_json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=root_circuit_json_data,
        expected_counts_before={
            Circuit: 1,
        },
        expected_counts_after={
            Circuit: 0,
        },
    )


@pytest.fixture
def entity_id_cascades(db, root_circuit_json_data, person_id):
    entity_id = add_db(
        db,
        Circuit(
            **root_circuit_json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
            }
        ),
    ).id
    external_url_id = add_db(
        db,
        ExternalUrl(
            name="url",
            description="url-description",
            source=ExternalSource.channelpedia,
            url="https://foo.bar",
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    ).id
    add_db(
        db,
        ScientificArtifactExternalUrlLink(
            scientific_artifact_id=entity_id,
            external_url_id=external_url_id,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    publication_id = add_db(
        db,
        Publication(
            DOI="foo",
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    ).id
    add_db(
        db,
        ScientificArtifactPublicationLink(
            scientific_artifact_id=entity_id,
            publication_id=publication_id,
            publication_type=PublicationType.entity_source,
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    return entity_id


def test_deletion_cascades(db, clients, entity_id_cascades):
    check_deletion_cascades(
        db=db,
        route=ROUTE,
        clients=clients,
        entity_id=entity_id_cascades,
        expected_counts_before={
            Circuit: 1,
            ExternalUrl: 1,
            Publication: 1,
            ScientificArtifactExternalUrlLink: 1,
            ScientificArtifactPublicationLink: 1,
        },
        expected_counts_after={
            Circuit: 0,
            ExternalUrl: 1,
            Publication: 1,
            ScientificArtifactExternalUrlLink: 0,
            ScientificArtifactPublicationLink: 0,
        },
    )


def test_read_many_1(client, circuit, circuit_json_data):
    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]

    # circuit and root circuit
    assert len(data) == 2

    circuit_data = next(d for d in data if d["id"] == str(circuit.id))
    _assert_read_response(circuit_data, circuit_json_data)


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, root_circuit_json_data):
    # using root_circuit_json_data to avoid the implication of creating two circuits
    # because of the root_circuit_id in circuit_json_data which messes up the check assumptions
    check_authorization(
        ROUTE, client_user_1, client_user_2, client_no_project, root_circuit_json_data
    )


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(db, circuit_json_data, person_id):
    booleans = [True, False, True, False, True, False]

    scales = [
        CircuitScale.single,
        CircuitScale.microcircuit,
        CircuitScale.whole_brain,
        CircuitScale.single,
        CircuitScale.microcircuit,
        CircuitScale.whole_brain,
    ]
    categories = [
        CircuitBuildCategory.computational_model,
        CircuitBuildCategory.em_reconstruction,
        CircuitBuildCategory.computational_model,
        CircuitBuildCategory.em_reconstruction,
        CircuitBuildCategory.computational_model,
        CircuitBuildCategory.em_reconstruction,
    ]

    db_circuits = [
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
                    "authorized_project_id": PROJECT_ID,
                    "published_in": f"journal-{i}",
                }
            )
        )
        for i, (bool_value, scale, category) in enumerate(
            zip(booleans, scales, categories, strict=False)
        )
    ]

    add_all_db(db, db_circuits)

    return db_circuits


def test_filtering(client, root_circuit, models):
    data = assert_request(
        client.get, url=ROUTE, params={"root_circuit_id": str(root_circuit.id)}
    ).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "root_circuit_id": str(root_circuit.id),
            "has_morphologies": True,
        },
    ).json()["data"]
    assert len(data) == 3

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "root_circuit_id": str(root_circuit.id),
            "has_morphologies": True,
            "has_point_neurons": False,
        },
    ).json()["data"]
    assert len(data) == 0

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "root_circuit_id": str(root_circuit.id),
            "build_category": "computational_model",
            "number_neurons__lte": 11,
        },
    ).json()["data"]
    assert len(data) == 1

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "root_circuit_id": str(root_circuit.id),
            "scale__in": ["single", "whole_brain"],
        },
    ).json()["data"]
    assert len(data) == 4

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "root_circuit_id": str(root_circuit.id),
            "subject__species__name": "Test Species",
        },
    ).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "root_circuit_id": str(root_circuit.id),
            "subject__species__name": "Unknown",
        },
    ).json()["data"]
    assert len(data) == 0

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"ilike_search": "*circuit-description*"},
    ).json()["data"]
    assert len(data) == len(models) + 1  # root circuit

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"ilike_search": "circuit-2"},
    ).json()["data"]
    assert len(data) == 1

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"published_in": "journal-0"},
    ).json()["data"]
    assert len(data) == 1

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"published_in__ilike": "journal"},
    ).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get, url=ROUTE, params={"target_simulator": TargetSimulator.neuron}
    ).json()["data"]
    assert len(data) == len(models)  # root is different than children

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"lifecycle_status": "active", "root_circuit_id": str(root_circuit.id)},
    ).json()["data"]
    assert len(data) == len(models)


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


def test_filter_by_derivation_type(db, client, root_circuit, circuit, public_circuit, person_id):
    """Filter circuits by derivation type on both the generated and used sides."""
    # circuit is derived from root_circuit via extraction; public_circuit via rewiring.
    # => root_circuit is the `used` (source) side of both derivations.
    _add_derivation(
        db,
        used_id=root_circuit.id,
        generated_id=circuit.id,
        person_id=person_id,
        derivation_type=DerivationType.circuit_extraction,
    )
    _add_derivation(
        db,
        used_id=root_circuit.id,
        generated_id=public_circuit.id,
        person_id=person_id,
        derivation_type=DerivationType.circuit_rewiring,
    )

    def ids(params):
        return {
            d["id"] for d in assert_request(client.get, url=ROUTE, params=params).json()["data"]
        }

    # --- generated side: "how this circuit was derived"
    assert ids({"generated_derivation__derivation_type": "circuit_extraction"}) == {str(circuit.id)}
    assert ids({"generated_derivation__derivation_type": "circuit_rewiring"}) == {
        str(public_circuit.id)
    }
    matched = ids(
        {"generated_derivation__derivation_type__in": ["circuit_extraction", "circuit_rewiring"]}
    )
    assert matched == {str(circuit.id), str(public_circuit.id)}
    # the underived root_circuit is not on the generated side of any derivation
    assert str(root_circuit.id) not in matched
    assert ids({"generated_derivation__derivation_type": "circuit_customization"}) == set()

    # --- used side: "what was derived from this circuit"
    assert ids({"used_derivation__derivation_type": "circuit_extraction"}) == {str(root_circuit.id)}
    assert ids({"used_derivation__derivation_type": "circuit_rewiring"}) == {str(root_circuit.id)}
    assert ids(
        {"used_derivation__derivation_type__in": ["circuit_extraction", "circuit_rewiring"]}
    ) == {str(root_circuit.id)}
    # the derived children are not on the used side of these derivations
    assert ids({"used_derivation__derivation_type": "circuit_customization"}) == set()

    # the filter alone does not add derivation columns to the response
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"generated_derivation__derivation_type": "circuit_extraction"},
    ).json()["data"]
    assert "generated_derivations" not in data[0]
    assert "used_derivations" not in data[0]


def test_filter_by_derivation_type_non_circuit_source(db, client, circuit, emodel_id, person_id):
    """The filter has no source-type restriction: an emodel->circuit derivation matches."""
    _add_derivation(
        db,
        used_id=emodel_id,
        generated_id=circuit.id,
        person_id=person_id,
        derivation_type=DerivationType.emodel_circuit,
    )
    data = assert_request(
        client.get, url=ROUTE, params={"generated_derivation__derivation_type": "emodel_circuit"}
    ).json()["data"]
    assert {d["id"] for d in data} == {str(circuit.id)}


def test_expand_derivations(db, client, root_circuit, circuit, person_id):
    """`expand` opts into derivation lists, per direction, independently."""
    _add_derivation(
        db,
        used_id=root_circuit.id,
        generated_id=circuit.id,
        person_id=person_id,
        derivation_type=DerivationType.circuit_extraction,
        label="extracted",
    )

    def get_by_id(entity_id, params=None):
        data = assert_request(client.get, url=ROUTE, params=params or {}).json()["data"]
        return next(d for d in data if d["id"] == str(entity_id))

    # no expand -> fields are absent entirely (no extra query, no null columns)
    child = get_by_id(circuit.id)
    assert "generated_derivations" not in child
    assert "used_derivations" not in child

    # expand=generated_derivations -> populated on the child; other direction is null
    child = get_by_id(circuit.id, {"expand": "generated_derivations"})
    assert child["used_derivations"] is None
    assert len(child["generated_derivations"]) == 1
    entry = child["generated_derivations"][0]
    assert entry["used"]["id"] == str(root_circuit.id)
    assert entry["used"]["type"] == EntityType.circuit
    assert entry["derivation_type"] == DerivationType.circuit_extraction
    assert entry["label"] == "extracted"

    # expand=used_derivations -> populated on the parent; other direction is null
    parent = get_by_id(root_circuit.id, {"expand": "used_derivations"})
    assert parent["generated_derivations"] is None
    assert len(parent["used_derivations"]) == 1
    entry = parent["used_derivations"][0]
    assert entry["generated"]["id"] == str(circuit.id)
    assert entry["generated"]["type"] == EntityType.circuit
    assert entry["derivation_type"] == DerivationType.circuit_extraction
    assert entry["label"] == "extracted"

    # expand both -> a direction with no derivations is an empty list (not null)
    params = {"expand": ["generated_derivations", "used_derivations"]}
    child = get_by_id(circuit.id, params)
    parent = get_by_id(root_circuit.id, params)
    assert len(child["generated_derivations"]) == 1
    assert child["used_derivations"] == []
    assert parent["generated_derivations"] == []
    assert len(parent["used_derivations"]) == 1


def test_filter_and_expand_combined(db, client, root_circuit, circuit, public_circuit, person_id):
    """Filtering and expanding compose: filtered rows carry the expanded columns."""
    _add_derivation(
        db,
        used_id=root_circuit.id,
        generated_id=circuit.id,
        person_id=person_id,
        derivation_type=DerivationType.circuit_extraction,
    )
    _add_derivation(
        db,
        used_id=root_circuit.id,
        generated_id=public_circuit.id,
        person_id=person_id,
        derivation_type=DerivationType.circuit_rewiring,
    )

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "generated_derivation__derivation_type": "circuit_extraction",
            "expand": "generated_derivations",
        },
    ).json()["data"]
    assert {d["id"] for d in data} == {str(circuit.id)}
    assert data[0]["generated_derivations"][0]["used"]["id"] == str(root_circuit.id)
    assert data[0]["used_derivations"] is None


def test_derivation_filter_pagination_no_duplicates(
    db, client, root_circuit, circuit, public_circuit, person_id
):
    """A circuit matching multiple derivation rows must not repeat across pages.

    root_circuit is the `used` source of two extraction derivations, so the one-to-many
    filter join yields two rows for it. Pagination must still treat it as a single circuit:
    total_items counts distinct circuits and the duplicate join row must not spill it onto a
    second page (regression for the derivation-filter pagination bug).
    """
    _add_derivation(
        db,
        used_id=root_circuit.id,
        generated_id=circuit.id,
        person_id=person_id,
        derivation_type=DerivationType.circuit_extraction,
    )
    _add_derivation(
        db,
        used_id=root_circuit.id,
        generated_id=public_circuit.id,
        person_id=person_id,
        derivation_type=DerivationType.circuit_extraction,
    )

    params = {"used_derivation__derivation_type": "circuit_extraction"}

    # only root_circuit is the `used` side of an extraction derivation, despite two join rows
    first = assert_request(
        client.get, url=ROUTE, params={**params, "page": 1, "page_size": 1}
    ).json()
    assert first["pagination"]["total_items"] == 1
    assert [d["id"] for d in first["data"]] == [str(root_circuit.id)]

    # the duplicate join row must not place root_circuit on a second page too
    second = assert_request(
        client.get, url=ROUTE, params={**params, "page": 2, "page_size": 1}
    ).json()
    assert second["data"] == []
