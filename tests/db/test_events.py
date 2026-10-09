import uuid
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
    Cleanup is handled by the outer transaction in the `db` fixture.
    """
    connection = db.connection()
    session = Session(
        connection,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )
    yield session
    session.close()


@pytest.fixture
def asset1(real_db, morphology_id, user_id):
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
            created_by_id=user_id,
            updated_by_id=user_id,
            label="morphology",
            storage_type=StorageType.aws_s3_internal,
        ),
    )


@pytest.fixture
def asset2(real_db, morphology_id, user_id):
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
            created_by_id=user_id,
            updated_by_id=user_id,
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
    """Patch storage deletion and S3 client creation.

    ``delete_storage_objects`` is called once per storage type with the list of keys.
    """
    with (
        patch("app.db.events.delete_storage_objects") as mock_delete,
        patch("app.db.events.get_s3_client", return_value=Mock()),
    ):
        yield mock_delete


def _deleted_keys(mock_delete):
    """Return the set of all keys passed across every delete_storage_objects call."""
    keys: set[str] = set()
    for call in mock_delete.call_args_list:
        keys.update(call.kwargs["s3_keys"])
    return keys


def test_asset_s3_deleted_after_commit(real_db, asset1, mock_storage_delete):
    """Hard delete removes the S3 object after commit."""

    real_db.delete(asset1)
    real_db.flush()
    real_db.commit()

    mock_storage_delete.assert_called_once()
    assert _deleted_keys(mock_storage_delete) == {asset1.full_path}


def test_asset_delete_rollback_does_not_delete_s3(real_db, asset1, mock_storage_delete):
    """Rollback prevents S3 deletion."""
    real_db.delete(asset1)
    real_db.flush()
    real_db.rollback()

    mock_storage_delete.assert_not_called()


def test_multiple_assets_deleted_in_single_transaction(
    real_db, asset1, asset2, mock_storage_delete
):
    """All hard-deleted assets are cleaned up after commit, batched per storage type."""
    real_db.delete(asset1)
    real_db.delete(asset2)
    real_db.commit()

    # Both assets share a storage type, so they are deleted in a single batched call.
    mock_storage_delete.assert_called_once()
    assert _deleted_keys(mock_storage_delete) == {asset1.full_path, asset2.full_path}


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

    assert _deleted_keys(mock_storage_delete) == {asset1.full_path, asset2.full_path}


def test_after_rollback_clears_assets_to_delete_key(
    db, real_db, morphology_id, user_id, mock_storage_delete
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
            created_by_id=user_id,
            updated_by_id=user_id,
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
    """Allow DB commit to succeed even if S3 deletion fails."""
    mock_storage_delete.side_effect = RuntimeError("Simulated S3 failure")

    real_db.delete(asset1)
    real_db.delete(asset2)

    try:
        real_db.commit()
    except Exception:  # ruff:ignore[blind-except]
        pytest.fail("DB commit failed due to S3 deletion errors")

    mock_storage_delete.assert_called_once()


def test_directory_asset_deleted_via_prefix(real_db, morphology_id, user_id):
    """A directory asset is removed recursively via delete_directory_storage_objects."""
    directory = add_db(
        real_db,
        Asset(
            path="dir",
            full_path="/private/dir",
            status="created",
            is_directory=True,
            content_type="application/vnd.directory",
            size=0,
            sha256_digest=None,
            meta={},
            entity_id=morphology_id,
            created_by_id=user_id,
            updated_by_id=user_id,
            label="morphology",
            storage_type=StorageType.aws_s3_internal,
        ),
    )
    with (
        patch("app.db.events.delete_directory_storage_objects") as mock_dir_delete,
        patch("app.db.events.delete_storage_objects") as mock_file_delete,
        patch("app.db.events.get_s3_client", return_value=Mock()),
    ):
        real_db.delete(directory)
        real_db.commit()

    mock_dir_delete.assert_called_once()
    assert mock_dir_delete.call_args.kwargs["s3_prefix"] == directory.full_path
    # directory assets are not routed through the single-file batch delete
    mock_file_delete.assert_not_called()


def test_committed_child_asset_skipped_in_storage_cleanup(real_db, morphology_id, user_id):
    """A committed child asset (parent_id set) is skipped: covered by the parent prefix delete."""
    directory = add_db(
        real_db,
        Asset(
            path="dir",
            full_path="/private/dir",
            status="created",
            is_directory=True,
            content_type="application/vnd.directory",
            size=0,
            sha256_digest=None,
            meta={},
            entity_id=morphology_id,
            created_by_id=user_id,
            updated_by_id=user_id,
            label="morphology",
            storage_type=StorageType.aws_s3_internal,
        ),
    )
    child = add_db(
        real_db,
        Asset(
            path="dir/child",
            full_path="/private/dir/child",
            status="created",
            is_directory=False,
            content_type="application/swc",
            size=0,
            sha256_digest=None,
            meta={},
            entity_id=morphology_id,
            created_by_id=user_id,
            updated_by_id=user_id,
            label="directory_child",
            storage_type=StorageType.aws_s3_internal,
            parent_id=directory.id,
        ),
    )
    with (
        patch("app.db.events.delete_directory_storage_objects") as mock_dir_delete,
        patch("app.db.events.delete_storage_objects") as mock_file_delete,
        patch("app.db.events.get_s3_client", return_value=Mock()),
    ):
        real_db.delete(child)
        real_db.commit()

    # The child is skipped entirely: no directory prefix delete, no single-file delete.
    mock_dir_delete.assert_not_called()
    mock_file_delete.assert_not_called()


def test_uploading_asset_aborts_multipart(user_id, morphology_id):
    """_abort_multipart_upload aborts the multipart upload of an UPLOADING asset."""
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
        created_by_id=user_id,
        updated_by_id=user_id,
        label="morphology",
        storage_type=StorageType.aws_s3_internal,
    )
    storage_client_factory = Mock()
    with patch("app.db.events.multipart_upload_abort") as mock_abort:
        test_module._abort_multipart_upload(asset, storage_client_factory)

    mock_abort.assert_called_once_with(
        upload_id=upload_id,
        storage_type=asset.storage_type,
        s3_key=asset.full_path,
        storage_client_factory=storage_client_factory,
    )


def _make_asset(*, status=AssetStatus.CREATED, is_directory=False, parent_id=None, path="foo"):
    return Asset(
        path=path,
        full_path=f"/private/{path}",
        status=status,
        upload_meta={"upload_id": "id"} if status == AssetStatus.UPLOADING else None,
        is_directory=is_directory,
        content_type="application/vnd.directory" if is_directory else "application/swc",
        size=0,
        sha256_digest=None,
        meta={},
        entity_id=None,
        created_by_id=None,
        updated_by_id=None,
        label="morphology",
        storage_type=StorageType.aws_s3_internal,
        parent_id=parent_id,
    )


def test_plan_storage_cleanup():
    """Assets are grouped by storage action; skipped assets are omitted."""
    parent_id = uuid.uuid4()
    uploading_file = _make_asset(status=AssetStatus.UPLOADING, path="up.bin")
    uploading_child = _make_asset(status=AssetStatus.UPLOADING, parent_id=parent_id, path="c.bin")
    uploading_dir = _make_asset(status=AssetStatus.UPLOADING, is_directory=True, path="updir")
    committed_child = _make_asset(parent_id=parent_id, path="dir/child")
    committed_dir = _make_asset(is_directory=True, path="dir")
    committed_file = _make_asset(path="file.swc")

    plan = test_module.plan_storage_cleanup(
        [
            uploading_file,
            uploading_child,
            uploading_dir,
            committed_child,
            committed_dir,
            committed_file,
        ]
    )

    assert plan.uploads_to_abort == [uploading_file, uploading_child]
    assert plan.directories_to_delete == [committed_dir]
    assert plan.files_to_delete == [committed_file]


def test_plan_storage_cleanup_empty():
    plan = test_module.plan_storage_cleanup([])
    assert plan == test_module.StorageCleanupPlan([], [], [])


def test_uploading_child_asset_is_aborted_not_skipped(real_db, morphology_id, user_id):
    """An UPLOADING child is aborted (not skipped): its multipart upload must be cleaned up."""
    directory = Asset(
        path="updir",
        full_path="/private/updir",
        status=AssetStatus.UPLOADING,
        upload_meta=None,
        is_directory=True,
        content_type="application/vnd.directory",
        size=0,
        sha256_digest=None,
        meta={},
        entity_id=morphology_id,
        created_by_id=user_id,
        updated_by_id=user_id,
        label="morphology",
        storage_type=StorageType.aws_s3_internal,
    )
    # Attach the child through the ORM relationship so the delete-orphan cascade removes it first.
    directory.children = [
        Asset(
            path="updir/child.bin",
            full_path="/private/updir/child.bin",
            status=AssetStatus.UPLOADING,
            upload_meta={"upload_id": "child-upload-id"},
            is_directory=False,
            content_type="application/swc",
            size=0,
            sha256_digest=None,
            meta={},
            entity_id=morphology_id,
            created_by_id=user_id,
            updated_by_id=user_id,
            label="directory_child",
            storage_type=StorageType.aws_s3_internal,
        )
    ]
    add_db(real_db, directory)

    with (
        patch("app.db.events.multipart_upload_abort") as mock_abort,
        patch("app.db.events.delete_directory_storage_objects") as mock_dir_delete,
        patch("app.db.events.delete_storage_objects") as mock_file_delete,
        patch("app.db.events.get_s3_client", return_value=Mock()),
    ):
        real_db.delete(directory)
        real_db.commit()

    # The child's multipart upload is aborted even though it is a child asset.
    mock_abort.assert_called_once()
    assert mock_abort.call_args.kwargs["upload_id"] == "child-upload-id"
    # No committed prefix delete or file delete happens for an in-progress upload.
    mock_dir_delete.assert_not_called()
    mock_file_delete.assert_not_called()


def test_many_uploading_children_are_all_aborted(real_db, morphology_id, user_id):
    """Every child multipart upload is aborted (in parallel) when its directory is deleted."""
    n_children = 20
    directory = Asset(
        path="bigdir",
        full_path="/private/bigdir",
        status=AssetStatus.UPLOADING,
        upload_meta=None,
        is_directory=True,
        content_type="application/vnd.directory",
        size=0,
        sha256_digest=None,
        meta={},
        entity_id=morphology_id,
        created_by_id=user_id,
        updated_by_id=user_id,
        label="morphology",
        storage_type=StorageType.aws_s3_internal,
    )
    directory.children = [
        Asset(
            path=f"bigdir/child_{i}.bin",
            full_path=f"/private/bigdir/child_{i}.bin",
            status=AssetStatus.UPLOADING,
            upload_meta={"upload_id": f"upload-{i}"},
            is_directory=False,
            content_type="application/swc",
            size=0,
            sha256_digest=None,
            meta={},
            entity_id=morphology_id,
            created_by_id=user_id,
            updated_by_id=user_id,
            label="directory_child",
            storage_type=StorageType.aws_s3_internal,
        )
        for i in range(n_children)
    ]
    add_db(real_db, directory)

    with (
        patch("app.db.events.multipart_upload_abort") as mock_abort,
        patch("app.db.events.get_s3_client", return_value=Mock()),
    ):
        real_db.delete(directory)
        real_db.commit()

    aborted_ids = {call.kwargs["upload_id"] for call in mock_abort.call_args_list}
    assert aborted_ids == {f"upload-{i}" for i in range(n_children)}


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
    with patch("app.db.events.delete_storage_objects") as mock_delete:
        mock_delete.side_effect = RuntimeError("Simulated S3 failure")

        real_db.delete(asset1)
        real_db.commit()  # triggers after_commit

    # Now capture_loguru_messages contains the logged messages
    assert len(capture_loguru_messages) == 1

    log_msg = capture_loguru_messages[0]
    assert "Failed to delete storage object" in log_msg
    assert str(asset1.storage_type) in log_msg
    assert "Simulated S3 failure" in log_msg


def test_loguru_logging_on_multipart_abort_error(user_id, morphology_id, capture_loguru_messages):
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
        created_by_id=user_id,
        updated_by_id=user_id,
        label="morphology",
        storage_type=StorageType.aws_s3_internal,
    )
    with patch("app.db.events.multipart_upload_abort", side_effect=RuntimeError("abort failed")):
        test_module._abort_multipart_upload(asset, Mock())

    assert len(capture_loguru_messages) == 1
    log_msg = capture_loguru_messages[0]
    assert "Failed to abort multipart upload" in log_msg
    assert str(asset.id) in log_msg
    assert "abort failed" in log_msg
