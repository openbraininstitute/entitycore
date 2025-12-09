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
    "children": [
        {
            "id": 8,
            "acronym": "grey",
            "name": "Basic cell groups and regions",
            "children": [],
        },
        {
            "id": 42,
            "acronym": "blue",
            "name": "BlueRegion",
            "children": [
                {
                    "id": 64,
                    "acronym": "red",
                    "name": "RedRegion",
                    "children": [],
                }
            ],
        },
    ],
}

# from the within-search-ascendants-and-descendants.png drawing
SEARCH_HIERARCHY = {
    "id": 997,
    "acronym": "root",
    "name": "root",
    "children": [
        {
            "id": 7,
            "acronym": "RegionA",
            "name": "RegionA",
            "children": [
                {
                    "id": 8,
                    "acronym": "RegionA-1",
                    "name": "RegionA-1",
                    "children": [
                        {
                            "id": 9,
                            "acronym": "RegionA-1-1",
                            "name": "RegionA-1-1",
                            "children": [],
                        },
                        {
                            "id": 10,
                            "acronym": "RegionA-1-2",
                            "name": "RegionA-1-2",
                            "children": [],
                        },
                    ],
                },
                {
                    "id": 98,
                    "acronym": "RegionA-2",
                    "name": "RegionA-2",
                    "children": [
                        {
                            "id": 99,
                            "acronym": "RegionA-2-1",
                            "name": "RegionA-2-1",
                            "children": [],
                        },
                        {
                            "id": 100,
                            "acronym": "RegionA-2-2",
                            "name": "RegionA-2-2",
                            "children": [],
                        },
                    ],
                },
            ],
        },
        {
            "id": 17,
            "acronym": "RegionB",
            "name": "RegionB",
            "children": [
                {
                    "id": 18,
                    "acronym": "RegionB-1",
                    "name": "RegionB-1",
                    "children": [],
                },
                {
                    "id": 20,
                    "acronym": "RegionB-2",
                    "name": "RegionB-1",
                    "children": [],
                },
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


def test_brain_region_id(db, client, client_admin, person_id, species_id):
    hierarchy_name = utils.create_hiearchy_name(
        db, name="test_hierarchy", species_id=species_id, created_by_id=person_id
    )
    utils.add_brain_region_hierarchy(db, HIERARCHY, hierarchy_name.id)

    response = client.get(ROUTE)
    assert response.status_code == 200
    response = response.json()
    assert len(response["data"]) == 4
    species = {
        "created_by": {
            "family_name": None,
            "given_name": None,
            "id": ANY,
            "pref_label": "Admin User",
            "sub_id": "00000000-0000-0000-0000-000000000000",
            "type": "person",
        },
        "creation_date": ANY,
        "id": ANY,
        "name": "Test Species",
        "taxonomy_id": "12345",
        "update_date": ANY,
        "updated_by": {
            "family_name": None,
            "given_name": None,
            "id": ANY,
            "pref_label": "Admin User",
            "sub_id": "00000000-0000-0000-0000-000000000000",
            "type": "person",
        },
    }

    assert response["data"] == [
        {
            "acronym": "grey",
            "color_hex_triplet": ANY,
            "creation_date": ANY,
            "annotation_value": 8,
            "hierarchy_id": str(hierarchy_name.id),
            "id": ANY,
            "name": "Basic cell groups and regions",
            "parent_structure_id": ANY,
            "update_date": ANY,
            "species": species,
            "strain": None,
        },
        {
            "acronym": "blue",
            "color_hex_triplet": ANY,
            "creation_date": ANY,
            "annotation_value": 42,
            "hierarchy_id": str(hierarchy_name.id),
            "id": ANY,
            "name": "BlueRegion",
            "parent_structure_id": ANY,
            "update_date": ANY,
            "species": species,
            "strain": None,
        },
        {
            "acronym": "red",
            "color_hex_triplet": ANY,
            "creation_date": ANY,
            "annotation_value": 64,
            "hierarchy_id": str(hierarchy_name.id),
            "id": ANY,
            "name": "RedRegion",
            "parent_structure_id": ANY,
            "update_date": ANY,
            "species": species,
            "strain": None,
        },
        {
            "acronym": "root",
            "color_hex_triplet": ANY,
            "creation_date": ANY,
            "annotation_value": 997,
            "hierarchy_id": str(hierarchy_name.id),
            "id": ANY,
            "name": "root",
            "parent_structure_id": None,
            "update_date": ANY,
            "species": species,
            "strain": None,
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


def test_family_queries(db, client, subject_id, person_id, species_id):
    hierarchy_name0 = utils.create_hiearchy_name(
        db, name="hier0", species_id=species_id, created_by_id=person_id
    )
    brain_regions0 = utils.add_brain_region_hierarchy(db, HIERARCHY, hierarchy_name0.id)

    hierarchy_name1 = utils.create_hiearchy_name(
        db, name="hier1", species_id=species_id, created_by_id=person_id
    )
    brain_regions1 = utils.add_brain_region_hierarchy(db, SEARCH_HIERARCHY, hierarchy_name1.id)

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
    assert len(client.get("/cell-morphology").json()["data"]) == 4 + 11

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

    for direction, region, expected in (
        ("descendants", "root", 4),
        ("descendants", "grey", 1),
        ("descendants", "blue", 2),
        ("descendants", "red", 1),
        ("ascendants", "root", 1),
        ("ascendants", "grey", 2),
        ("ascendants", "blue", 2),
        ("ascendants", "red", 3),
        ("ascendants_and_descendants", "root", 4),
        ("ascendants_and_descendants", "grey", 2),
        ("ascendants_and_descendants", "blue", 3),
        ("ascendants_and_descendants", "red", 3),
    ):
        response = get_response("hier0", region, direction=direction)
        assert len(response) == expected
        if direction != "ascendants_and_descendants":
            ascendants = direction == "ascendants"
            legacy = get_response("hier0", region, ascendants=ascendants)
            assert len(legacy) == expected

    for direction, region, expected in (
        ("descendants", "root", 11),
        ("descendants", "RegionA", 7),
        ("descendants", "RegionA-1", 3),
        ("descendants", "RegionA-1-1", 1),
        ("descendants", "RegionA-1-2", 1),
        ("descendants", "RegionA-2", 3),
        ("descendants", "RegionA-2-1", 1),
        ("descendants", "RegionA-2-2", 1),
        ("descendants", "RegionB", 3),
        ("descendants", "RegionB-1", 1),
        ("descendants", "RegionB-2", 1),
        ("ascendants", "root", 1),
        ("ascendants", "RegionA", 2),
        ("ascendants", "RegionA-1", 3),
        ("ascendants", "RegionA-1-1", 4),
        ("ascendants", "RegionA-1-2", 4),
        ("ascendants", "RegionA-2", 3),
        ("ascendants", "RegionA-2-1", 4),
        ("ascendants", "RegionA-2-2", 4),
        ("ascendants", "RegionB", 2),
        ("ascendants", "RegionB-1", 3),
        ("ascendants", "RegionB-2", 3),
        ("ascendants_and_descendants", "root", 11),
        ("ascendants_and_descendants", "RegionA", 8),
        ("ascendants_and_descendants", "RegionA-1", 5),
        ("ascendants_and_descendants", "RegionA-1-1", 4),
        ("ascendants_and_descendants", "RegionA-1-2", 4),
        ("ascendants_and_descendants", "RegionA-2", 5),
        ("ascendants_and_descendants", "RegionA-2-1", 4),
        ("ascendants_and_descendants", "RegionA-2-2", 4),
        ("ascendants_and_descendants", "RegionB", 4),
        ("ascendants_and_descendants", "RegionB-1", 3),
        ("ascendants_and_descendants", "RegionB-2", 3),
    ):
        response = get_response("hier1", region, direction=direction)
        assert len(response) == expected
