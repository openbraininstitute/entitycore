from unittest.mock import Mock, patch

import pytest
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import object_session

from app.db import events as test_module
from app.db.model import Asset
from app.db.types import AssetStatus, StorageType

from tests.utils import add_db


@pytest.fixture
def real_db(db):
    """Independent session on the same connection with real commit/rollback semantics.

    Shares the underlying connection with `db` so it can see unflushed fixture data,
    while having its own savepoint that fires after_commit/after_rollback events.
    """
    connection = db.connection()
    savepoint = connection.begin_nested()
    session = Session(bind=connection, expire_on_commit=False, autocommit=False, autoflush=False)
    session.begin_nested()  # inner savepoint so session.rollback() only rolls back to here
    yield session
    session.close()
    savepoint.rollback()


@pytest.fixture
def asset1(real_db, morphology_id, person_id):
    """First persisted Asset."""
    return add_db(
        real_db,
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
def asset2(real_db, morphology_id, person_id):
    """Second persisted Asset."""
    return add_db(
        real_db,
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


def test_collect_asset_for_storage_deletion__adds_asset_to_session_info(real_db, asset1):
    """Asset attached to a session is added to ASSETS_TO_DELETE_KEY."""

    # Sanity: asset is attached to a session
    session = object_session(asset1)
    assert session is real_db

    # Act
    test_module.collect_asset_for_storage_deletion(None, None, asset1)

    # Assert
    assert test_module.ASSETS_TO_DELETE_KEY in real_db.info
    assert asset1 in real_db.info[test_module.ASSETS_TO_DELETE_KEY]


def test_collect_asset_for_storage_deletion__logs_warning_when_no_session():
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
        test_module.collect_asset_for_storage_deletion(None, None, asset)

        mock_warning.assert_called_once()
        args, _ = mock_warning.call_args
        assert "not attached to a session" in args[0]


@pytest.fixture
def mock_storage_delete():
    """Patch storage deletion and S3 client creation."""
    with (
        patch("app.db.events.delete_asset_storage_object") as mock_delete,
        patch("app.db.events.get_s3_client", return_value=Mock()),
    ):
        yield mock_delete


def test_asset_s3_deleted_after_commit(real_db, asset1, mock_storage_delete):
    """Hard delete removes the S3 object after commit."""

    real_db.delete(asset1)
    real_db.flush()
    real_db.commit()

    mock_storage_delete.assert_called_once()
    assert mock_storage_delete.call_args.kwargs["s3_key"] == asset1.full_path


def test_asset_delete_rollback_does_not_delete_s3(real_db, asset1, mock_storage_delete):
    """Rollback prevents S3 deletion."""
    real_db.delete(asset1)
    real_db.flush()
    real_db.rollback()

    mock_storage_delete.assert_not_called()


def test_multiple_assets_deleted_in_single_transaction(
    real_db, asset1, asset2, mock_storage_delete
):
    """All hard-deleted assets are cleaned up after commit."""
    real_db.delete(asset1)
    real_db.delete(asset2)
    real_db.commit()

    assert mock_storage_delete.call_count == 2
    deleted_ids = {call.kwargs["s3_key"] for call in mock_storage_delete.call_args_list}
    assert deleted_ids == {asset1.full_path, asset2.full_path}


def test_s3_error_does_not_break_transaction(real_db, asset1, mock_storage_delete):
    """Ensure S3 deletion errors do not prevent DB commit."""
    mock_storage_delete.side_effect = RuntimeError("Simulated S3 failure")

    real_db.delete(asset1)

    # Commit should succeed without raising
    real_db.commit()

    mock_storage_delete.assert_called_once()

    # Verify that the asset was actually deleted from the database
    assert not real_db.get(Asset, asset1.id)


def test_multiple_flushes_accumulate_assets(real_db, asset1, asset2, mock_storage_delete):
    """Collect all assets deleted across multiple flushes for deletion."""
    real_db.delete(asset1)
    real_db.flush()
    real_db.delete(asset2)
    real_db.commit()

    deleted_ids = {call.kwargs["s3_key"] for call in mock_storage_delete.call_args_list}
    assert deleted_ids == {asset1.full_path, asset2.full_path}


def test_after_rollback_clears_assets_to_delete_key(
    db, real_db, morphology_id, person_id, mock_storage_delete
):
    """Clear session info key after rollback to allow future deletes."""
    # Insert via shared db so asset survives the real_db rollback
    asset = add_db(
        db,
        Asset(
            path="baz",
            full_path="/baz",
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
    asset_in_real_db = real_db.get(Asset, asset.id)
    real_db.delete(asset_in_real_db)
    real_db.rollback()

    # The info dict should no longer have the key
    assert test_module.ASSETS_TO_DELETE_KEY not in real_db.info
    mock_storage_delete.assert_not_called()

    # The same asset can be deleted again in a new transaction after rollback
    asset_in_real_db = real_db.get(Asset, asset.id)
    real_db.delete(asset_in_real_db)
    real_db.commit()
    mock_storage_delete.assert_called_once()


def test_multiple_assets_s3_failure_does_not_break_transaction(
    real_db, asset1, asset2, mock_storage_delete
):
    """Allow DB commit to succeed even if multiple S3 deletions fail."""
    mock_storage_delete.side_effect = RuntimeError("Simulated S3 failure")

    real_db.delete(asset1)
    real_db.delete(asset2)

    try:
        real_db.commit()
    except Exception:  # ruff:ignore[blind-except]
        pytest.fail("DB commit failed due to S3 deletion errors")

    assert mock_storage_delete.call_count == 2


def test_partial_s3_failure_does_not_stop_others(real_db, asset1, asset2, mock_storage_delete):
    """Attempt deletion of all assets even if some S3 deletions fail."""

    def side_effect(*args, **kwargs):  # ruff:ignore[unused-function-argument]
        if kwargs.get("s3_key") == asset1.full_path:
            msg = "S3 error"
            raise RuntimeError(msg)

    mock_storage_delete.side_effect = side_effect

    real_db.delete(asset1)
    real_db.delete(asset2)
    real_db.commit()

    # Both assets attempted
    assert mock_storage_delete.call_count == 2


def test_delete_asset_from_storage__created_status(person_id, morphology_id):
    """_delete_asset_from_storage calls delete_asset_storage_object for a non-uploading asset."""
    asset = Asset(
        path="foo",
        full_path="/foo",
        status=AssetStatus.CREATED,
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
    )
    storage_client_factory = Mock()
    with patch("app.db.events.delete_asset_storage_object") as mock_delete:
        test_module._delete_asset_from_storage(asset, storage_client_factory)

    mock_delete.assert_called_once_with(
        storage_type=asset.storage_type,
        s3_key=asset.full_path,
        storage_client_factory=storage_client_factory,
    )


def test_delete_asset_from_storage__uploading_status(person_id, morphology_id):
    """_delete_asset_from_storage calls multipart_upload_abort for an uploading asset."""
    upload_id = "test-upload-id"
    asset = Asset(
        path="foo",
        full_path="/foo",
        status=AssetStatus.UPLOADING,
        upload_meta={"upload_id": upload_id},
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
    )
    storage_client_factory = Mock()
    with patch("app.db.events.multipart_upload_abort") as mock_abort:
        test_module._delete_asset_from_storage(asset, storage_client_factory)

    mock_abort.assert_called_once_with(
        upload_id=upload_id,
        storage_type=asset.storage_type,
        s3_key=asset.full_path,
        storage_client_factory=storage_client_factory,
    )


@pytest.fixture
def capture_loguru_messages():
    """Capture log messages emitted by Loguru during a test."""
    messages = []

    # Add a sink that appends formatted messages to the list
    handler_id = logger.add(messages.append, level="ERROR")
    yield messages
    logger.remove(handler_id)


def test_loguru_logging_on_s3_deletion_error(real_db, asset1, capture_loguru_messages):
    """Check that Loguru records the exception when S3 deletion fails."""
    with patch("app.db.events.delete_asset_storage_object") as mock_delete:
        mock_delete.side_effect = RuntimeError("Simulated S3 failure")

        real_db.delete(asset1)
        real_db.commit()  # triggers after_commit

    # Now capture_loguru_messages contains the logged messages
    assert len(capture_loguru_messages) == 1

    log_msg = capture_loguru_messages[0]
    assert "Failed to delete storage object" in log_msg
    assert str(asset1.id) in log_msg
    assert "Simulated S3 failure" in log_msg


def test_loguru_logging_on_multipart_abort_error(person_id, morphology_id, capture_loguru_messages):
    """Check that Loguru records the exception when multipart abort fails."""
    asset = Asset(
        path="foo",
        full_path="/foo",
        status=AssetStatus.UPLOADING,
        upload_meta={"upload_id": "test-upload-id"},
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
    )
    with patch("app.db.events.multipart_upload_abort", side_effect=RuntimeError("abort failed")):
        test_module._delete_asset_from_storage(asset, Mock())

    assert len(capture_loguru_messages) == 1
    log_msg = capture_loguru_messages[0]
    assert "Failed to abort multipart upload" in log_msg
    assert str(asset.id) in log_msg
    assert "abort failed" in log_msg
