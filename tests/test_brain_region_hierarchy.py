import operator

from tests import test_brain_region
from tests.utils import MISSING_ID, MISSING_ID_COMPACT

ROUTE = "/brain-region-hierarchy"


def test_brain_region_hierarchy(client, brain_region_hierarchy_id):
    response = client.get(f"{ROUTE}/{brain_region_hierarchy_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AIBS"
    assert data["id"] == str(brain_region_hierarchy_id)

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "AIBS"
    assert data[0]["id"] == str(brain_region_hierarchy_id)


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422


def test_hierarchy_tree(db, client, brain_region_hierarchy_id):
    test_brain_region.add_brain_region_hierarchy(
        db, test_brain_region.HIERARCHY, brain_region_hierarchy_id
    )

    response = client.get(f"{ROUTE}/{brain_region_hierarchy_id}/hierarchy")
    assert response.status_code == 200
    data = response.json()

    def compare_hier(raw_node, service_node):
        assert raw_node["id"] == service_node["annotation_value"]
        for name in ("acronym", "color_hex_triplet", "name"):
            assert raw_node[name] == service_node[name]
            if "children" in raw_node or "children" in service_node:
                for rn, sn in zip(
                    sorted(raw_node["children"], key=operator.itemgetter("acronym")),
                    sorted(service_node["children"], key=operator.itemgetter("acronym")),
                    strict=False,
                ):
                    compare_hier(rn, sn)

    compare_hier(test_brain_region.HIERARCHY, data)
