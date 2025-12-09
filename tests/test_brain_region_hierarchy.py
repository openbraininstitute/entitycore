import operator

import pytest

from app.db.model import BrainRegionHierarchy

from .utils import check_creation_fields
from tests import test_brain_region, utils
from tests.utils import (
    check_global_delete_one,
    check_global_read_one,
    check_global_update_one,
)

ROUTE = "/brain-region-hierarchy"
ADMIN_ROUTE = "/admin/brain-region-hierarchy"


@pytest.fixture
def json_data(species_id):
    return {
        "name": "my-hierarchy",
        "species_id": species_id,
    }


def _assert_read_response(data, json_data):
    assert "id" in data
    assert data["name"] == json_data["name"]
    assert "created_by" in data
    assert "updated_by" in data


def test_brain_region_hierarchy(client, brain_region_hierarchy_id):
    response = client.get(f"{ROUTE}/{brain_region_hierarchy_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AIBS"
    assert data["id"] == str(brain_region_hierarchy_id)
    utils.check_creation_fields(data)

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "AIBS"
    assert data[0]["id"] == str(brain_region_hierarchy_id)
    utils.check_creation_fields(data[0])


def test_missing(client):
    response = client.get(f"{ROUTE}/{utils.MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{utils.MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/{utils.MISSING_ID}/hierarchy")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{utils.MISSING_ID_COMPACT}/hierarchy")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242/hierarchy")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber/hierarchy")
    assert response.status_code == 422


def test_hierarchy_tree(db, client, brain_region_hierarchy_id):
    utils.add_brain_region_hierarchy(db, test_brain_region.HIERARCHY, brain_region_hierarchy_id)

    response = client.get(f"{ROUTE}/{brain_region_hierarchy_id}/hierarchy")
    assert response.status_code == 200
    data = response.json()

    def compare_hier(raw_node, service_node):
        assert raw_node["id"] == service_node["annotation_value"]
        for name in ("acronym", "name"):
            assert raw_node[name] == service_node[name]
            if "children" in raw_node or "children" in service_node:
                for rn, sn in zip(
                    sorted(raw_node["children"], key=operator.itemgetter("acronym")),
                    sorted(service_node["children"], key=operator.itemgetter("acronym")),
                    strict=False,
                ):
                    compare_hier(rn, sn)

    compare_hier(test_brain_region.HIERARCHY, data)


def test_create(client, client_admin, species_id):
    count = 3
    items = []
    for i in range(count):
        name = f"Test brain-region-hierarchy {i}"
        response = client_admin.post(ROUTE, json={"name": name, "species_id": species_id})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name
        check_creation_fields(data)
        assert "id" in data
        items.append(data)

    response = client.get(f"{ROUTE}/{items[0]['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data == items[0]
    check_creation_fields(data)

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count
    assert data == items
    check_creation_fields(data[0])

    # test filter
    response = client.get(ROUTE, params={"name": "Test brain-region-hierarchy 1"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data == [items[1]]
    check_creation_fields(data[0])

    response = client.get(ROUTE, params={"species__id": str(species_id)})
    assert len(response.json()["data"]) == 3

    response = client.get(ROUTE, params={"species__id": "00000000-7000-4000-0000-000000000000"})
    assert len(response.json()["data"]) == 0


def test_read_one(clients, json_data):
    check_global_read_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        validator=_assert_read_response,
    )


def test_update_one(clients, json_data):
    check_global_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={
            "name": "my-new-brain-region-hierarchy",
        },
    )


def test_delete_one(db, clients, json_data):
    check_global_delete_one(
        db=db,
        clients=clients,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        json_data=json_data,
        expected_counts_before={
            BrainRegionHierarchy: 1,
        },
        expected_counts_after={
            BrainRegionHierarchy: 0,
        },
    )
