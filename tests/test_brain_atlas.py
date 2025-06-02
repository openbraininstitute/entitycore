import itertools as it
from unittest.mock import ANY

from app.db.model import BrainAtlas, BrainAtlasRegion
from app.db.types import EntityType

from . import utils

ROUTE = "/brain-atlas"
FILE_EXAMPLE_PATH = utils.TEST_DATA_DIR / "example.json"


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
    with FILE_EXAMPLE_PATH.open("rb") as f:
        utils.upload_entity_asset(
            client,
            EntityType.brain_atlas,
            brain_atlas0.id,
            files={"file": ("a/b/c.txt", f, "text/plain")},
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
        "assets": [
            {
                "content_type": "text/plain",
                "full_path": ANY,
                "id": ANY,
                "is_directory": False,
                "label": None,
                "meta": {},
                "path": "a/b/c.txt",
                "sha256_digest": "a8124f083a58b9a8ff80cb327dd6895a10d0bc92bb918506da0c9c75906d3f91",
                "size": 31,
                "status": "created",
            }
        ],
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

    data = (("root", False, None), ("blue", False, None), ("red", True, 15), ("grey", True, 10))
    ids = {}
    for brain_atlas, (name, leaf, volume) in it.product(
        (brain_atlas0, brain_atlas1),
        data,
    ):
        row = BrainAtlasRegion(
            volume=volume,
            is_leaf_region=leaf,
            brain_region_id=regions[name].id,
            brain_atlas_id=brain_atlas.id,
            authorized_project_id=utils.PROJECT_ID,
            authorized_public=True,
        )
        ids[brain_atlas.name, name] = utils.add_db(db, row)

        with FILE_EXAMPLE_PATH.open("rb") as f:
            utils.upload_entity_asset(
                client,
                EntityType.brain_atlas_region,
                entity_id=ids[brain_atlas.name, name].id,
                files={"file": ("a/b/c.txt", f, "text/plain")},
            ).raise_for_status()

    response = client.get(
        f"{ROUTE}/{brain_atlas0.id}/regions", params={"order_by": "+creation_date"}
    )
    assert response.status_code == 200
    expected_asset = {
        "content_type": "text/plain",
        "full_path": ANY,
        "id": ANY,
        "is_directory": False,
        "label": None,
        "meta": {},
        "path": "a/b/c.txt",
        "sha256_digest": "a8124f083a58b9a8ff80cb327dd6895a10d0bc92bb918506da0c9c75906d3f91",
        "size": 31,
        "status": "created",
    }
    assert response.json()["data"] == [
        {
            "assets": [expected_asset],
            "brain_atlas_id": str(brain_atlas0.id),
            "brain_region_id": str(regions["root"].id),
            "creation_date": ANY,
            "id": str(ids[brain_atlas0.name, "root"].id),
            "is_leaf_region": False,
            "update_date": ANY,
            "volume": None,
        },
        {
            "assets": [expected_asset],
            "brain_atlas_id": str(brain_atlas0.id),
            "brain_region_id": str(regions["blue"].id),
            "creation_date": ANY,
            "id": str(ids[brain_atlas0.name, "blue"].id),
            "is_leaf_region": False,
            "update_date": ANY,
            "volume": None,
        },
        {
            "assets": [expected_asset],
            "brain_atlas_id": str(brain_atlas0.id),
            "brain_region_id": str(regions["red"].id),
            "creation_date": ANY,
            "id": str(ids[brain_atlas0.name, "red"].id),
            "is_leaf_region": True,
            "update_date": ANY,
            "volume": 15.0,
        },
        {
            "assets": [expected_asset],
            "brain_atlas_id": str(brain_atlas0.id),
            "brain_region_id": str(regions["grey"].id),
            "creation_date": ANY,
            "id": str(ids[brain_atlas0.name, "grey"].id),
            "is_leaf_region": True,
            "update_date": ANY,
            "volume": 10.0,
        },
    ]

    response = client.get(f"{ROUTE}/{brain_atlas0.id}/regions/{ids[brain_atlas0.name, 'root'].id}")
    assert response.status_code == 200
    assert response.json() == {
        "assets": [expected_asset],
        "brain_atlas_id": str(brain_atlas0.id),
        "brain_region_id": str(regions["root"].id),
        "creation_date": ANY,
        "id": str(ids[brain_atlas0.name, "root"].id),
        "is_leaf_region": False,
        "update_date": ANY,
        "volume": None,
    }
