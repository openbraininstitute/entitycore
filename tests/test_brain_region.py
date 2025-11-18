import itertools as it
from unittest.mock import ANY

import pytest

from app.db.model import BrainRegion, BrainRegionHierarchy

from . import utils

ROUTE = "/brain-region"
ADMIN_ROUTE = "/admin/brain-region"


HIERARCHY = {
    "id": 997,
    "acronym": "root",
    "name": "root",
    "color_hex_triplet": "FFFFFF",
    "parent_structure_id": None,
    "children": [
        {
            "id": 8,
            "acronym": "grey",
            "name": "Basic cell groups and regions",
            "color_hex_triplet": "BFDAE3",
            "parent_structure_id": 997,
            "children": [],
        },
        {
            "id": 42,
            "acronym": "blue",
            "name": "BlueRegion",
            "color_hex_triplet": "0000FF",
            "parent_structure_id": 997,
            "children": [
                {
                    "id": 64,
                    "acronym": "red",
                    "name": "RedRegion",
                    "color_hex_triplet": "FF0000",
                    "parent_structure_id": 42,
                    "children": [],
                }
            ],
        },
    ],
}


@pytest.fixture
def json_data(brain_region_hierarchy_id):
    return {
        "name": "my-region",
        "acronym": "grey",
        "color_hex_triplet": "BFDAE3",
        "annotation_value": 9999,
        "hierarchy_id": str(brain_region_hierarchy_id),
    }


def _assert_read_response(data, json_data):
    assert data["name"] == json_data["name"]
    assert data["acronym"] == json_data["acronym"]
    assert data["color_hex_triplet"] == json_data["color_hex_triplet"]
    assert data["annotation_value"] == json_data["annotation_value"]


def test_create_one(client_admin, json_data):
    data = utils.assert_request(client_admin.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_read_one(clients, json_data):
    utils.check_global_read_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        validator=_assert_read_response,
    )


def test_update_one(clients, json_data):
    utils.check_global_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={"annotation_value": 800, "acronym": "blue"},
    )


def test_delete_one(db, clients, json_data):
    utils.check_global_delete_one(
        db=db,
        clients=clients,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        json_data=json_data,
        expected_counts_before={
            BrainRegion: 1,
            BrainRegionHierarchy: 1,
        },
        expected_counts_after={
            BrainRegion: 0,
            BrainRegionHierarchy: 1,
        },
    )


def test_brain_region_id(db, client, client_admin, person_id):
    hierarchy_name = utils.create_hiearchy_name(db, "test_hierarchy", created_by_id=person_id)
    utils.add_brain_region_hierarchy(db, HIERARCHY, hierarchy_name.id)

    response = client.get(ROUTE)
    assert response.status_code == 200
    response = response.json()
    assert len(response["data"]) == 4
    assert response["data"] == [
        {
            "acronym": "grey",
            "color_hex_triplet": "BFDAE3",
            "creation_date": ANY,
            "annotation_value": 8,
            "hierarchy_id": str(hierarchy_name.id),
            "id": ANY,
            "name": "Basic cell groups and regions",
            "parent_structure_id": ANY,
            "update_date": ANY,
        },
        {
            "acronym": "blue",
            "color_hex_triplet": "0000FF",
            "creation_date": ANY,
            "annotation_value": 42,
            "hierarchy_id": str(hierarchy_name.id),
            "id": ANY,
            "name": "BlueRegion",
            "parent_structure_id": ANY,
            "update_date": ANY,
        },
        {
            "acronym": "red",
            "color_hex_triplet": "FF0000",
            "creation_date": ANY,
            "annotation_value": 64,
            "hierarchy_id": str(hierarchy_name.id),
            "id": ANY,
            "name": "RedRegion",
            "parent_structure_id": ANY,
            "update_date": ANY,
        },
        {
            "acronym": "root",
            "color_hex_triplet": "FFFFFF",
            "creation_date": ANY,
            "annotation_value": 997,
            "hierarchy_id": str(hierarchy_name.id),
            "id": ANY,
            "name": "root",
            "parent_structure_id": None,
            "update_date": ANY,
        },
    ]

    response = client.get(ROUTE + "?acronym=root")
    assert response.status_code == 200
    root_id = response.json()["data"][0]["id"]

    response = client.get(f"{ROUTE}/{root_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["annotation_value"] == 997
    assert data["name"] == "root"
    assert data["acronym"] == "root"

    response = client_admin.get(f"{ADMIN_ROUTE}/{root_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["annotation_value"] == 997
    assert data["name"] == "root"
    assert data["acronym"] == "root"

    # test semantic_search
    response = client.get(ROUTE, params={"semantic_search": "Blue region"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 4  # semantic search just reorders - it does not filter out


def test_family_queries(db, client, subject_id, person_id):
    hierarchy_name0 = utils.create_hiearchy_name(db, "hier0", created_by_id=person_id)
    brain_regions0 = utils.add_brain_region_hierarchy(db, HIERARCHY, hierarchy_name0.id)

    hierarchy_name1 = utils.create_hiearchy_name(db, "hier1", created_by_id=person_id)
    brain_regions1 = utils.add_brain_region_hierarchy(db, HIERARCHY, hierarchy_name1.id)

    for acronym, row in it.chain(brain_regions0.items(), brain_regions1.items()):
        hier = "hier0" if row.hierarchy_id == hierarchy_name0.id else "hier1"
        utils.create_cell_morphology_id(
            client,
            subject_id=subject_id,
            brain_region_id=row.id,
            authorized_public=False,
            name=f"{acronym}-{hier}",
            description=f"Description {acronym}-{hier}",
        )
    assert len(client.get("/cell-morphology").json()["data"]) == 8

    def get_response(hier, acronym, ascendants=False, direction=None):  # noqa: FBT002
        hierarchy_id = hierarchy_name0.id if hier == "hier0" else hierarchy_name1.id
        brain_region_id = (
            brain_regions0[acronym].id if hier == "hier0" else brain_regions1[acronym].id
        )

        params = {
            "within_brain_region_hierarchy_id": hierarchy_id,
            "within_brain_region_brain_region_id": brain_region_id,
            "within_brain_region_ascendants": ascendants,
        }
        if direction is not None:
            params["within_brain_region_direction"] = direction

        return client.get("/cell-morphology", params=params).json()["data"]

    for hier in ("hier0", "hier1"):
        # descendants
        old = get_response(hier, "root", ascendants=False)
        response = get_response(hier, "root", direction="descendants")
        assert len(old) == len(response) == 4

        old = get_response(hier, "grey", ascendants=False)
        response = get_response(hier, "grey", direction="descendants")
        assert len(old) == len(response) == 1

        old = get_response(hier, "blue", ascendants=False)
        response = get_response(hier, "blue", direction="descendants")
        assert len(old) == len(response) == 2

        old = get_response(hier, "red", ascendants=False)
        response = get_response(hier, "red", direction="descendants")
        assert len(old) == len(response) == 1

        # ascendants
        old = get_response(hier, "root", ascendants=True)
        response = get_response(hier, "root", direction="ascendants")
        assert len(old) == len(response) == 1

        old = get_response(hier, "grey", ascendants=True)
        response = get_response(hier, "grey", direction="ascendants")
        assert len(old) == len(response) == 2

        old = get_response(hier, "blue", ascendants=True)
        response = get_response(hier, "blue", direction="ascendants")
        assert len(old) == len(response) == 2

        old = get_response(hier, "red", ascendants=True)
        response = get_response(hier, "red", direction="ascendants")
        assert len(old) == len(response) == 3

        # ascendants_and_descendants
        response = get_response(hier, "root", direction="ascendants_and_descendants")
        assert len(response) == 4

        response = get_response(hier, "grey", direction="ascendants_and_descendants")
        assert len(response) == 2

        response = get_response(hier, "blue", direction="ascendants_and_descendants")
        assert len(response) == 3

        response = get_response(hier, "red", direction="ascendants_and_descendants")
        assert len(response) == 3
