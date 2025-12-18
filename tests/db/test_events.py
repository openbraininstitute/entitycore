from unittest.mock import Mock, patch

import pytest
from loguru import logger
from sqlalchemy.orm.session import object_session

from app.db import events, events as test_module
from app.db.events import ASSETS_TO_DELETE_KEY
from app.db.model import Asset
from app.db.types import StorageType

from tests.utils import add_db


@pytest.fixture
def asset1(db, morphology_id, person_id):
    """First persisted Asset."""
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


@pytest.fixture
def asset2(db, morphology_id, person_id):
    """Second persisted Asset."""
    return add_db(
        db,
        Asset(
            path="bar",
            full_path="/bar",
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


def test_asset_before_delete__adds_asset_to_session_info(db, asset1):
    """Asset attached to a session is added to ASSETS_TO_DELETE_KEY."""

    # Sanity: asset is attached to a session
    session = object_session(asset1)
    assert session is db

    # Act
    test_module.asset_before_delete(None, None, asset1)

    # Assert
    assert ASSETS_TO_DELETE_KEY in db.info
    assert asset1 in db.info[ASSETS_TO_DELETE_KEY]


def test_asset_before_delete__logs_warning_when_no_session():
    """Logs a warning if the asset is not attached to a session."""

    asset = Asset(
        path="foo",
        full_path="/foo",
        status="created",
        is_directory=False,
        content_type="application/swc",
        size=0,
        sha256_digest=None,
        meta={},
        entity_id=1,
        created_by_id=1,
        updated_by_id=1,
        label="morphology",
        storage_type=StorageType.aws_s3_internal,
    )

    with patch("app.db.events.L.warning") as mock_warning:
        test_module.asset_before_delete(None, None, asset)

        mock_warning.assert_called_once()
        args, _ = mock_warning.call_args
        assert "not attached to a session" in args[0]


@pytest.fixture
def mock_storage_delete():
    """Patch storage deletion and S3 client creation."""
    with (
        patch("app.db.events.delete_asset_storage_object") as mock_delete,
        patch("app.utils.s3.get_s3_client", return_value=Mock()),
    ):
        yield mock_delete


def test_asset_s3_deleted_after_commit(db, asset1, mock_storage_delete):
    """Hard delete removes the S3 object after commit."""

    db.delete(asset1)
    db.flush()
    db.commit()

    mock_storage_delete.assert_called_once()
    assert mock_storage_delete.call_args.kwargs["s3_key"] == asset1.full_path


def test_asset_delete_rollback_does_not_delete_s3(db, asset1, mock_storage_delete):
    """Rollback prevents S3 deletion."""
    db.delete(asset1)
    db.flush()
    db.rollback()

    mock_storage_delete.assert_not_called()


def test_multiple_assets_deleted_in_single_transaction(db, asset1, asset2, mock_storage_delete):
    """All hard-deleted assets are cleaned up after commit."""
    db.delete(asset1)
    db.delete(asset2)
    db.commit()

    assert mock_storage_delete.call_count == 2
    deleted_ids = {call.kwargs["s3_key"] for call in mock_storage_delete.call_args_list}
    assert deleted_ids == {asset1.full_path, asset2.full_path}


def test_s3_error_does_not_break_transaction(db, asset1, mock_storage_delete):
    """Ensure S3 deletion errors do not prevent DB commit."""
    mock_storage_delete.side_effect = RuntimeError("Simulated S3 failure")

    db.delete(asset1)

    # Commit should succeed without raising
    db.commit()

    mock_storage_delete.assert_called_once()

    # Verify that the asset was actually deleted from the database
    assert not db.get(Asset, asset1.id)


def test_multiple_flushes_accumulate_assets(db, asset1, asset2, mock_storage_delete):
    """Collect all assets deleted across multiple flushes for deletion."""
    db.delete(asset1)
    db.flush()
    db.delete(asset2)
    db.commit()

    deleted_ids = {call.kwargs["s3_key"] for call in mock_storage_delete.call_args_list}
    assert deleted_ids == {asset1.full_path, asset2.full_path}


def test_after_rollback_clears_assets_to_delete_key(db, asset1, mock_storage_delete):
    """Clear session info key after rollback to allow future deletes."""
    db.delete(asset1)
    db.rollback()

    # The info dict should no longer have the key
    assert events.ASSETS_TO_DELETE_KEY not in db.info

    # Deleting a new asset after rollback works normally
    db.delete(asset1)
    db.commit()
    mock_storage_delete.assert_called_once()


def test_multiple_assets_s3_failure_does_not_break_transaction(
    db, asset1, asset2, mock_storage_delete
):
    """Allow DB commit to succeed even if multiple S3 deletions fail."""
    mock_storage_delete.side_effect = RuntimeError("Simulated S3 failure")

    db.delete(asset1)
    db.delete(asset2)

    try:
        db.commit()
    except Exception:  # noqa: BLE001
        pytest.fail("DB commit failed due to S3 deletion errors")

    assert mock_storage_delete.call_count == 2


def test_partial_s3_failure_does_not_stop_others(db, asset1, asset2, mock_storage_delete):
    """Attempt deletion of all assets even if some S3 deletions fail."""

    def side_effect(asset, _):
        if asset.id == asset1.id:
            msg = "S3 error"
            raise RuntimeError(msg)

    mock_storage_delete.side_effect = side_effect

    db.delete(asset1)
    db.delete(asset2)
    db.commit()

    # Both assets attempted
    assert mock_storage_delete.call_count == 2


@pytest.fixture
def capture_loguru_messages():
    """Capture log messages emitted by Loguru during a test."""
    messages = []

    # Add a sink that appends formatted messages to the list
    handler_id = logger.add(messages.append, level="ERROR")
    yield messages
    logger.remove(handler_id)


def test_loguru_logging_on_s3_deletion_error(db, asset1, capture_loguru_messages):
    """Check that Loguru records the exception when S3 deletion fails."""
    with patch("app.db.events.delete_asset_storage_object") as mock_delete:
        mock_delete.side_effect = RuntimeError("Simulated S3 failure")

        db.delete(asset1)
        db.commit()  # triggers after_commit

    # Now capture_loguru_messages contains the logged messages
    assert len(capture_loguru_messages) == 1

    log_msg = capture_loguru_messages[0]
    assert "Failed to delete storage object" in log_msg
    assert str(asset1.id) in log_msg
    assert "Simulated S3 failure" in log_msg
