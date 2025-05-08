import itertools as it
from unittest.mock import ANY

import sqlalchemy as sa

from app.db.model import BrainRegion

from . import utils

ROUTE = "/brain-region"


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

    ids = {None: None}
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

    ret = {row.acronym: row for row in db.execute(sa.select(BrainRegion)).scalars()}
    return ret


def test_brain_region_id(db, client):
    hierarchy_name = utils.create_hiearchy_name(db, "test_hierarchy")
    add_brain_region_hierarchy(db, HIERARCHY, hierarchy_name.id)

    response = client.get(ROUTE)
    assert response.status_code == 200
    response = response.json()
    assert len(response["data"]) == 4
    assert response["data"] == [
        {
            "acronym": "root",
            "color_hex_triplet": "FFFFFF",
            "creation_date": ANY,
            "hierarchy_id": 997,
            "hierarchy_name_id": str(hierarchy_name.id),
            "id": ANY,
            "name": "root",
            "parent_structure_id": None,
            "update_date": ANY,
        },
        {
            "acronym": "blue",
            "color_hex_triplet": "0000FF",
            "creation_date": ANY,
            "hierarchy_id": 42,
            "hierarchy_name_id": str(hierarchy_name.id),
            "id": ANY,
            "name": "BlueRegion",
            "parent_structure_id": ANY,
            "update_date": ANY,
        },
        {
            "acronym": "red",
            "color_hex_triplet": "FF0000",
            "creation_date": ANY,
            "hierarchy_id": 64,
            "hierarchy_name_id": str(hierarchy_name.id),
            "id": ANY,
            "name": "RedRegion",
            "parent_structure_id": ANY,
            "update_date": ANY,
        },
        {
            "acronym": "grey",
            "color_hex_triplet": "BFDAE3",
            "creation_date": ANY,
            "hierarchy_id": 8,
            "hierarchy_name_id": str(hierarchy_name.id),
            "id": ANY,
            "name": "Basic cell groups and regions",
            "parent_structure_id": ANY,
            "update_date": ANY,
        },
    ]

    response = client.get(ROUTE + "?acronym=root")
    assert response.status_code == 200
    root_id = response.json()["data"][0]["id"]

    response = client.get(f"{ROUTE}/{root_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["hierarchy_id"] == 997
    assert data["name"] == "root"
    assert data["acronym"] == "root"


def test_family_queries(db, client, species_id, strain_id):
    hierarchy_name0 = utils.create_hiearchy_name(db, "hier0")
    brain_regions0 = add_brain_region_hierarchy(db, HIERARCHY, hierarchy_name0.id)

    hierarchy_name1 = utils.create_hiearchy_name(db, "hier1")
    brain_regions1 = add_brain_region_hierarchy(db, HIERARCHY, hierarchy_name1.id)

    for acronym, row in it.chain(brain_regions0.items(), brain_regions1.items()):
        hier = "hier0" if row.hierarchy_name_id == hierarchy_name0.id else "hier1"
        utils.create_reconstruction_morphology_id(
            client,
            species_id=species_id,
            strain_id=strain_id,
            brain_region_id=row.id,
            authorized_public=False,
            name=f"{acronym}-{hier}",
            description=f"Description {acronym}-{hier}",
        )
    assert len(client.get("/reconstruction-morphology").json()["data"]) == 8

    def get_response(hier, acronym, ascendents):
        hierarchy_name_id = hierarchy_name0.id if hier == "hier0" else hierarchy_name1.id
        brain_region_id = (
            brain_regions0[acronym].id if hier == "hier0" else brain_regions1[acronym].id
        )

        url = (
            "/reconstruction-morphology"
            f"?within_brain_region_hierachy_name_id={hierarchy_name_id}"
            f"&within_brain_region_brain_region_id={brain_region_id}"
            f"&within_brain_region_ascendants={ascendents}"
        )
        return client.get(url)

    for hier in ("hier0", "hier1"):
        # descendents
        response = get_response(hier, "root", ascendents=False)
        assert len(response.json()["data"]) == 4

        response = get_response(hier, "grey", ascendents=False)
        assert len(response.json()["data"]) == 1

        response = get_response(hier, "blue", ascendents=False)
        assert len(response.json()["data"]) == 2

        response = get_response(hier, "red", ascendents=False)
        assert len(response.json()["data"]) == 1

        # ascendents
        response = get_response(hier, "root", ascendents=True)
        assert len(response.json()["data"]) == 1

        response = get_response(hier, "grey", ascendents=True)
        assert len(response.json()["data"]) == 2

        response = get_response(hier, "blue", ascendents=True)
        assert len(response.json()["data"]) == 2

        response = get_response(hier, "red", ascendents=True)
        assert len(response.json()["data"]) == 3
