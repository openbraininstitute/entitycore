import io
import uuid

import pytest
import sqlalchemy as sa

from app.config import storages
from app.db.model import Asset, Entity
from app.db.types import EntityType, StorageType
from app.utils.s3 import PRIVATE_ASSET_PREFIX, PUBLIC_ASSET_PREFIX, build_s3_path

from tests.utils import (
    PROJECT_ID,
    VIRTUAL_LAB_ID,
    add_db,
    assert_request,
    s3_key_exists,
    upload_entity_asset,
)

PUBLISH_URL = "/admin/publish-project"
UNPUBLISH_URL = "/admin/unpublish-project"


@pytest.fixture
def private_morphology_with_asset(
    client, subject_id, brain_region_id, cell_morphology_protocol_id, tmp_path
):
    entity_id = assert_request(
        client.post,
        url="/cell-morphology",
        json={
            "name": "Private Morphology",
            "description": "desc",
            "brain_region_id": str(brain_region_id),
            "cell_morphology_protocol_id": str(cell_morphology_protocol_id),
            "subject_id": str(subject_id),
            "location": {"x": 0, "y": 0, "z": 0},
            "authorized_public": False,
        },
    ).json()["id"]

    filepath = tmp_path / "morph.asc"
    filepath.write_bytes(b"morphology data")
    upload_entity_asset(
        client=client,
        entity_type=EntityType.cell_morphology,
        entity_id=entity_id,
        files={"file": ("morph.asc", filepath.read_bytes(), "application/asc")},
        label="morphology",
    )
    return uuid.UUID(entity_id)


@pytest.fixture
def private_circuit_with_directory_asset(db, s3, circuit, person_id):
    s3_path = build_s3_path(
        vlab_id=VIRTUAL_LAB_ID,
        proj_id=PROJECT_ID,
        entity_type=EntityType.circuit,
        entity_id=circuit.id,
        filename="my-directory",
        is_public=False,
    )
    bucket = storages[StorageType.aws_s3_internal].bucket
    directory_files = ["circuit_config.json", "nodes.h5", "edges.h5"]
    for fname in directory_files:
        s3.upload_fileobj(io.BytesIO(b"data"), Bucket=bucket, Key=f"{s3_path}/{fname}")

    asset = add_db(
        db,
        Asset(
            path="my-directory",
            full_path=s3_path,
            status="created",
            is_directory=True,
            content_type="application/vnd.directory",
            size=0,
            sha256_digest=None,
            meta={},
            entity_id=circuit.id,
            created_by_id=person_id,
            updated_by_id=person_id,
            label="sonata_circuit",
            storage_type=StorageType.aws_s3_internal,
        ),
    )
    return circuit.id, asset.id, directory_files


def _get_entity(db, entity_id):
    return db.execute(sa.select(Entity).where(Entity.id == entity_id)).scalar_one()


def _get_asset(db, entity_id):
    return db.execute(sa.select(Asset).where(Asset.entity_id == entity_id)).scalar_one()


def _publish(client, project_id, *, dry_run=False, max_assets=None):
    params = {"dry_run": dry_run}
    if max_assets is not None:
        params["max_assets"] = max_assets
    return client.post(f"{PUBLISH_URL}/{project_id}", params=params)


def _unpublish(client, project_id, *, dry_run=False, max_assets=None):
    params = {"dry_run": dry_run}
    if max_assets is not None:
        params["max_assets"] = max_assets
    return client.post(f"{UNPUBLISH_URL}/{project_id}", params=params)


def test_publish(db, client_admin, s3, private_morphology_with_asset):
    entity_id = private_morphology_with_asset

    asset_before = _get_asset(db, entity_id)
    old_path = asset_before.full_path
    assert old_path.startswith(PRIVATE_ASSET_PREFIX)
    assert s3_key_exists(s3, key=old_path)

    response = _publish(client_admin, PROJECT_ID, dry_run=False)
    assert response.status_code == 200
    data = response.json()

    assert data["public"] is True
    assert data["dry_run"] is False
    # resource_count can be > 1 in case there are other resources besides the morphology
    assert data["resource_count"] >= 1
    assert data["move_assets_result"]["asset_count"] == 1
    assert data["move_assets_result"]["file_count"] == 1
    assert data["move_assets_result"]["total_size"] > 0
    assert data["completed"] is True

    db.expire_all()
    entity = _get_entity(db, entity_id)
    assert entity.authorized_public is True

    asset = _get_asset(db, entity_id)
    assert asset.full_path.startswith(PUBLIC_ASSET_PREFIX)
    assert s3_key_exists(s3, key=asset.full_path)
    assert not s3_key_exists(s3, key=old_path)


def test_publish_dry_run(db, client_admin, private_morphology_with_asset):
    entity_id = private_morphology_with_asset

    response = _publish(client_admin, PROJECT_ID, dry_run=True)
    assert response.status_code == 200
    data = response.json()

    assert data["project_id"] == PROJECT_ID
    assert data["public"] is True
    assert data["dry_run"] is True
    # resource_count can be > 1 in case there are other resources besides the morphology
    assert data["resource_count"] >= 1
    assert data["completed"] is True

    db.expire_all()
    entity = _get_entity(db, entity_id)
    assert entity.authorized_public is False

    asset = _get_asset(db, entity_id)
    assert asset.full_path.startswith(PRIVATE_ASSET_PREFIX)


@pytest.mark.usefixtures("private_morphology_with_asset")
def test_publish_with_max_assets(client_admin):
    response = _publish(client_admin, PROJECT_ID, dry_run=False, max_assets=1)
    assert response.status_code == 200
    data = response.json()
    assert data["move_assets_result"]["asset_count"] == 1
    assert data["completed"] is False

    response = _publish(client_admin, PROJECT_ID, dry_run=False, max_assets=1)
    assert response.status_code == 200
    data = response.json()
    assert data["move_assets_result"]["asset_count"] == 0
    assert data["completed"] is True


def test_publish_no_resources(client_admin):
    empty_project_id = str(uuid.uuid4())
    response = _publish(client_admin, empty_project_id, dry_run=False)
    assert response.status_code == 200
    data = response.json()
    assert data["resource_count"] == 0
    assert data["move_assets_result"]["asset_count"] == 0
    assert data["completed"] is True


def test_unpublish(db, client_admin, s3, private_morphology_with_asset):
    entity_id = private_morphology_with_asset

    _publish(client_admin, PROJECT_ID, dry_run=False)
    db.expire_all()

    asset_before = _get_asset(db, entity_id)
    old_path = asset_before.full_path
    assert old_path.startswith(PUBLIC_ASSET_PREFIX)
    assert s3_key_exists(s3, key=old_path)

    response = _unpublish(client_admin, PROJECT_ID, dry_run=False)
    assert response.status_code == 200
    data = response.json()

    assert data["public"] is False
    assert data["dry_run"] is False
    # resource_count can be > 1 in case there are other resources besides the morphology
    assert data["resource_count"] >= 1
    assert data["move_assets_result"]["asset_count"] == 1
    assert data["completed"] is True

    db.expire_all()
    entity = _get_entity(db, entity_id)
    assert entity.authorized_public is False

    asset = _get_asset(db, entity_id)
    assert asset.full_path.startswith(PRIVATE_ASSET_PREFIX)
    assert s3_key_exists(s3, key=asset.full_path)
    assert not s3_key_exists(s3, key=old_path)


def test_unpublish_dry_run(db, client_admin, private_morphology_with_asset):
    entity_id = private_morphology_with_asset

    _publish(client_admin, PROJECT_ID, dry_run=False)
    db.expire_all()

    response = _unpublish(client_admin, PROJECT_ID, dry_run=True)
    assert response.status_code == 200
    data = response.json()

    assert data["public"] is False
    assert data["dry_run"] is True

    db.expire_all()
    entity = _get_entity(db, entity_id)
    assert entity.authorized_public is True

    asset = _get_asset(db, entity_id)
    assert asset.full_path.startswith(PUBLIC_ASSET_PREFIX)


def test_publish_then_unpublish(db, client_admin, s3, private_morphology_with_asset):
    entity_id = private_morphology_with_asset

    asset_before = _get_asset(db, entity_id)
    original_path = asset_before.full_path

    _publish(client_admin, PROJECT_ID, dry_run=False)
    db.expire_all()
    assert _get_entity(db, entity_id).authorized_public is True
    assert _get_asset(db, entity_id).full_path.startswith(PUBLIC_ASSET_PREFIX)

    _unpublish(client_admin, PROJECT_ID, dry_run=False)
    db.expire_all()
    assert _get_entity(db, entity_id).authorized_public is False

    asset_after = _get_asset(db, entity_id)
    assert asset_after.full_path.startswith(PRIVATE_ASSET_PREFIX)
    assert asset_after.full_path == original_path
    assert s3_key_exists(s3, key=asset_after.full_path)


def test_publish_directory_asset(db, client_admin, s3, private_circuit_with_directory_asset):
    _entity_id, asset_id, directory_files = private_circuit_with_directory_asset

    asset_before = db.get(Asset, asset_id)
    old_path = asset_before.full_path
    assert old_path.startswith(PRIVATE_ASSET_PREFIX)
    for fname in directory_files:
        assert s3_key_exists(s3, key=f"{old_path}/{fname}")

    response = _publish(client_admin, PROJECT_ID, dry_run=False)
    assert response.status_code == 200
    data = response.json()
    assert data["move_assets_result"]["file_count"] == len(directory_files)

    db.expire_all()
    asset_after = db.get(Asset, asset_id)
    assert asset_after.full_path.startswith(PUBLIC_ASSET_PREFIX)
    for fname in directory_files:
        assert s3_key_exists(s3, key=f"{asset_after.full_path}/{fname}")
        assert not s3_key_exists(s3, key=f"{old_path}/{fname}")


def test_unpublish_directory_asset(db, client_admin, s3, private_circuit_with_directory_asset):
    _entity_id, asset_id, directory_files = private_circuit_with_directory_asset

    asset_before = db.get(Asset, asset_id)
    original_path = asset_before.full_path

    _publish(client_admin, PROJECT_ID, dry_run=False)
    db.expire_all()

    public_path = db.get(Asset, asset_id).full_path
    assert public_path.startswith(PUBLIC_ASSET_PREFIX)

    _unpublish(client_admin, PROJECT_ID, dry_run=False)
    db.expire_all()

    asset_after = db.get(Asset, asset_id)
    assert asset_after.full_path == original_path
    for fname in directory_files:
        assert s3_key_exists(s3, key=f"{asset_after.full_path}/{fname}")
        assert not s3_key_exists(s3, key=f"{public_path}/{fname}")
