import itertools as it
from unittest.mock import ANY

import pytest

from app.db.model import BrainAtlas, BrainAtlasRegion
from app.db.types import EntityType, StorageType

from . import utils

ROUTE = "/brain-atlas"
ADMIN_ROUTE = "/admin/brain-atlas"
MODEL = BrainAtlas
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


def test_brain_atlas(db, client, species_id, person_id):
    hierarchy_name = utils.create_hiearchy_name(
        db, name="test_hierarchy", created_by_id=person_id, species_id=species_id
    )
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
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    with FILE_EXAMPLE_PATH.open("rb") as f:
        utils.upload_entity_asset(
            client,
            EntityType.brain_atlas,
            brain_atlas0.id,
            files={"file": ("annotation.nrrd", f, "application/nrrd")},
            label="brain_atlas_annotation",
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
            created_by_id=person_id,
            updated_by_id=person_id,
        ),
    )
    expected = {
        "assets": [
            {
                "content_type": "application/nrrd",
                "full_path": ANY,
                "id": ANY,
                "is_directory": False,
                "label": "brain_atlas_annotation",
                "meta": {},
                "path": "annotation.nrrd",
                "sha256_digest": "a8124f083a58b9a8ff80cb327dd6895a10d0bc92bb918506da0c9c75906d3f91",
                "size": 31,
                "status": "created",
                "storage_type": StorageType.aws_s3_internal,
            }
        ],
        "creation_date": ANY,
        "hierarchy_id": str(hierarchy_name.id),
        "id": str(brain_atlas0.id),
        "name": "test brain atlas",
        "description": "test brain atlas description",
        "species": {
            "id": species_id,
            "name": "Test Species",
            "taxonomy_id": "12345",
        },
        "update_date": ANY,
        "created_by": ANY,
        "updated_by": ANY,
        "authorized_project_id": utils.PROJECT_ID,
        "authorized_public": True,
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
            created_by_id=person_id,
            updated_by_id=person_id,
        )
        ids[brain_atlas.name, name] = utils.add_db(db, row)

        with FILE_EXAMPLE_PATH.open("rb") as f:
            utils.upload_entity_asset(
                client,
                EntityType.brain_atlas_region,
                entity_id=ids[brain_atlas.name, name].id,
                files={"file": ("mesh.obj", f, "application/obj")},
                label="brain_atlas_region_mesh",
            ).raise_for_status()

    response = client.get(
        f"{ROUTE}/{brain_atlas0.id}/regions", params={"order_by": "+creation_date"}
    )
    assert response.status_code == 200
    expected_asset = {
        "content_type": "application/obj",
        "full_path": ANY,
        "id": ANY,
        "is_directory": False,
        "label": "brain_atlas_region_mesh",
        "meta": {},
        "path": "mesh.obj",
        "sha256_digest": "a8124f083a58b9a8ff80cb327dd6895a10d0bc92bb918506da0c9c75906d3f91",
        "size": 31,
        "status": "created",
        "storage_type": StorageType.aws_s3_internal,
    }
    assert response.json()["data"] == [
        {
            "assets": [expected_asset],
            "authorized_project_id": utils.PROJECT_ID,
            "authorized_public": True,
            "brain_atlas_id": str(brain_atlas0.id),
            "brain_region_id": str(regions["root"].id),
            "created_by": ANY,
            "creation_date": ANY,
            "id": str(ids[brain_atlas0.name, "root"].id),
            "is_leaf_region": False,
            "updated_by": ANY,
            "update_date": ANY,
            "volume": None,
        },
        {
            "assets": [expected_asset],
            "authorized_project_id": utils.PROJECT_ID,
            "authorized_public": True,
            "brain_atlas_id": str(brain_atlas0.id),
            "brain_region_id": str(regions["blue"].id),
            "created_by": ANY,
            "creation_date": ANY,
            "id": str(ids[brain_atlas0.name, "blue"].id),
            "is_leaf_region": False,
            "updated_by": ANY,
            "update_date": ANY,
            "volume": None,
        },
        {
            "assets": [expected_asset],
            "authorized_project_id": utils.PROJECT_ID,
            "authorized_public": True,
            "brain_atlas_id": str(brain_atlas0.id),
            "brain_region_id": str(regions["red"].id),
            "created_by": ANY,
            "creation_date": ANY,
            "id": str(ids[brain_atlas0.name, "red"].id),
            "is_leaf_region": True,
            "updated_by": ANY,
            "update_date": ANY,
            "volume": 15.0,
        },
        {
            "assets": [expected_asset],
            "authorized_project_id": utils.PROJECT_ID,
            "authorized_public": True,
            "brain_atlas_id": str(brain_atlas0.id),
            "brain_region_id": str(regions["grey"].id),
            "created_by": ANY,
            "creation_date": ANY,
            "id": str(ids[brain_atlas0.name, "grey"].id),
            "is_leaf_region": True,
            "updated_by": ANY,
            "update_date": ANY,
            "volume": 10.0,
        },
    ]

    # call with default order_by
    response = client.get(
        f"{ROUTE}/{brain_atlas0.id}/regions",
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) == 4

    response = client.get(f"{ROUTE}/{brain_atlas0.id}/regions/{ids[brain_atlas0.name, 'root'].id}")
    assert response.status_code == 200
    assert response.json() == {
        "assets": [expected_asset],
        "authorized_project_id": utils.PROJECT_ID,
        "authorized_public": True,
        "brain_atlas_id": str(brain_atlas0.id),
        "brain_region_id": str(regions["root"].id),
        "created_by": ANY,
        "creation_date": ANY,
        "id": str(ids[brain_atlas0.name, "root"].id),
        "is_leaf_region": False,
        "updated_by": ANY,
        "update_date": ANY,
        "volume": None,
    }


@pytest.fixture
def json_data(brain_region_hierarchy_id, species_id):
    return {
        "name": "test brain atlas",
        "description": "a magnificent description",
        "hierarchy_id": str(brain_region_hierarchy_id),
        "species_id": str(species_id),
    }


@pytest.fixture
def model(db, json_data, person_id):
    return utils.add_db(
        db,
        MODEL(
            **json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": str(utils.PROJECT_ID),
            },
        ),
    )


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return utils.assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


def _assert_read_response(data, json_data):
    assert "id" in data
    assert "authorized_public" in data
    assert "authorized_project_id" in data
    assert "assets" in data
    assert data["name"] == json_data["name"]
    assert data["description"] == json_data["description"]
    assert data["hierarchy_id"] == json_data["hierarchy_id"]

    utils.check_creation_fields(data)


def test_update_one(clients, json_data):
    utils.check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={
            "name": "new name!",
        },
        optional_payload=None,
    )


def test_create_one(client, json_data):
    data = utils.assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_user_read_one(client, model, json_data):
    data = utils.assert_request(client.get, url=f"{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_admin_read_one(client_admin, model, json_data):
    data = utils.assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_read_many(client, model, json_data):
    data = utils.assert_request(client.get, url=f"{ROUTE}").json()["data"]

    assert len(data) == 1

    assert data[0]["id"] == str(model.id)
    _assert_read_response(data[0], json_data)


def test_delete_one(db, clients, json_data):
    utils.check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={
            MODEL: 1,
        },
        expected_counts_after={
            MODEL: 0,
        },
    )


def test_missing(client):
    utils.check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    utils.check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    utils.check_pagination(ROUTE, client, create_id)
