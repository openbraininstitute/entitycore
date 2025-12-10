from unittest.mock import patch

import pytest

from app.db.model import Asset
from app.db.types import StorageType
from app.utils.s3 import get_s3_client

from tests.utils import add_db


@pytest.fixture
def asset(db, morphology_id, person_id):
    return add_db(
        db,
        Asset(
            path="foo",
            full_path="/foo",
            status="created",
            is_directory=False,
            content_type="application/swc",
            size=0,
            sha256_digest=None,
            meta={},
            entity_id=morphology_id,
            created_by_id=person_id,
            updated_by_id=person_id,
            label="morphology",
            storage_type=StorageType.aws_s3_internal,
        ),
    )


def test_delete_asset_storage_object_event(db, asset):
    with patch("app.db.events.delete_asset_storage_object") as mock_delete:
        # Act: delete ORM instance
        db.delete(asset)
        db.flush()

    # Assert: event listener was triggered
    mock_delete.assert_called_once_with(asset=asset, storage_client_factory=get_s3_client)
