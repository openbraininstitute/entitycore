import itertools as it
from unittest.mock import ANY

import pytest

from app.db.model import BrainAtlas, BrainAtlasRegion

from . import utils

ROUTE = "/brain-atlas"


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
def asdf():
    pass


def test_brain_atlas(db, client, species_id):
    hierarchy_name = utils.create_hiearchy_name(db, "test_hierarchy")
    regions = utils.add_brain_region_hierarchy(db, HIERARCHY, hierarchy_name.id)

    brain_atlas0 = utils.add_db(
        db,
        BrainAtlas(
            name="test brain atlas",
            description="test brain atlas description",
            species_id=species_id,
            hierarchy_id=hierarchy_name.id,
            authorized_project_id=utils.PROJECT_ID,
            authorized_public=True,
        ),
    )
    brain_atlas1 = utils.add_db(
        db,
        BrainAtlas(
            name="test brain atlas 1",
            description="test brain atlas description 1",
            species_id=species_id,
            hierarchy_id=hierarchy_name.id,
            authorized_project_id=utils.PROJECT_ID,
            authorized_public=True,
        ),
    )
    expected = {
        "creation_date": ANY,
        "hierarchy_id": str(hierarchy_name.id),
        "id": str(brain_atlas0.id),
        "name": "test brain atlas",
        "species": {
            "creation_date": ANY,
            "id": species_id,
            "name": "Test Species",
            "taxonomy_id": "12345",
            "update_date": ANY,
        },
        "update_date": ANY,
    }

    response = client.get(ROUTE)
    assert response.status_code == 200
    response = response.json()
    assert len(response["data"]) == 2
    assert response["data"][0] == expected

    response = client.get(f"{ROUTE}/{brain_atlas0.id}")
    assert response.status_code == 200
    response = response.json()
    assert response == expected

    data = (("root", False, -1), ("blue", False, -1), ("red", True, 15), ("grey", True, 10))
    ids = {}
    for brain_atlas, (name, leaf, volume) in it.product(
        (
            brain_atlas0,
            brain_atlas1,
        ),
        data,
    ):
        row = BrainAtlasRegion(
            volume=volume,
            leaf_region=leaf,
            brain_region_id=regions[name].id,
            brain_atlas_id=brain_atlas.id,
            authorized_project_id=utils.PROJECT_ID,
            authorized_public=True,
        )
        ids[brain_atlas.name, name] = utils.add_db(db, row)

    response = client.get(
        f"{ROUTE}/{brain_atlas0.id}/regions", params={"order_by": "+creation_date"}
    )
    assert response.status_code == 200
    assert response.json()["data"] == [
        {
            "brain_atlas_id": str(brain_atlas0.id),
            "brain_region_id": str(regions["root"].id),
            "creation_date": ANY,
            "id": str(ids[brain_atlas0.name, "root"].id),
            "leaf_region": False,
            "update_date": ANY,
            "volume": -1.0,
        },
        {
            "brain_atlas_id": str(brain_atlas0.id),
            "brain_region_id": str(regions["blue"].id),
            "creation_date": ANY,
            "id": str(ids[brain_atlas0.name, "blue"].id),
            "leaf_region": False,
            "update_date": ANY,
            "volume": -1.0,
        },
        {
            "brain_atlas_id": str(brain_atlas0.id),
            "brain_region_id": str(regions["red"].id),
            "creation_date": ANY,
            "id": str(ids[brain_atlas0.name, "red"].id),
            "leaf_region": True,
            "update_date": ANY,
            "volume": 15.0,
        },
        {
            "brain_atlas_id": str(brain_atlas0.id),
            "brain_region_id": str(regions["grey"].id),
            "creation_date": ANY,
            "id": str(ids[brain_atlas0.name, "grey"].id),
            "leaf_region": True,
            "update_date": ANY,
            "volume": 10.0,
        },
    ]

    response = client.get(f"{ROUTE}/{brain_atlas0.id}/regions/{ids[brain_atlas0.name, 'root'].id}")
    assert response.status_code == 200
    assert response.json() == {
        "brain_atlas_id": str(brain_atlas0.id),
        "brain_region_id": str(regions["root"].id),
        "creation_date": ANY,
        "id": str(ids[brain_atlas0.name, "root"].id),
        "leaf_region": False,
        "update_date": ANY,
        "volume": -1.0,
    }
