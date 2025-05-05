from app.db.model import BrainRegion

from . import utils

ROUTE = "/brain-region"


def test_get_brain_region(client):
    response = client.get(ROUTE)
    assert response.status_code == 200
    assert len(response.text) > 4_500_000


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


def add_brain_region_hierarchy(db, hierarchy, hierarchy_name_id):
    regions = []

    def recurse(i):
        children = []
        item = i | {"children": children}
        for child in i["children"]:
            children.append(child["id"])
            recurse(child)
        regions.append(item)

    recurse(hierarchy)

    ids = {None: BrainRegion.ROOT_PARENT_UUID}
    for region in reversed(regions):
        row = BrainRegion(
            hierarchy_id=region["id"],
            acronym=region["acronym"],
            name=region["name"],
            color_hex_triplet=region["color_hex_triplet"],
            parent_structure_id=ids[region["parent_structure_id"]],
            hierarchy_name_id=hierarchy_name_id,
        )
        db_br = utils.add_db(db, row)
        db.flush()
        ids[region["id"]] = db_br.id

    return regions


def test_brain_region_id(db, client):
    hierarchy_name = utils.create_hiearchy_name(db, "test_hierarchy")
    add_brain_region_hierarchy(db, HIERARCHY, hierarchy_name.id)
    response = client.get(f"{ROUTE}/997")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 997
    assert data["name"] == "root"
    assert data["acronym"] == "root"
    assert data["children"] == [8, 42]

    response = client.get(ROUTE, params={"flat": True})
    assert response.status_code == 200
    data = response.json()
    assert data == [
        [997, "root", "root", [8, 42], 1],
        [8, "Basic cell groups and regions", "grey", [], 2],
        [42, "BlueRegion", "blue", [64], 2],
        [64, "RedRegion", "red", [], 3],
    ]
