import dataclasses
from collections import defaultdict
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import NamedTuple

from sqlalchemy import event
from sqlalchemy.orm import Session, SessionTransaction
from sqlalchemy.orm.session import object_session

from app.config import settings, storages
from app.db.model import Asset
from app.db.types import AssetStatus, StorageType
from app.logger import L
from app.utils.s3 import (
    StorageClientFactory,
    delete_directory_storage_objects,
    delete_storage_objects,
    get_s3_client,
    multipart_upload_abort,
)

ASSETS_TO_DELETE_KEY = "assets_to_delete_from_storage"


class StorageCleanupPlan(NamedTuple):
    """Deleted assets grouped by the storage action they require."""

    uploads_to_abort: list[Asset]
    directories_to_delete: list[Asset]
    files_to_delete: list[Asset]


def plan_storage_cleanup(assets: Iterable[Asset]) -> StorageCleanupPlan:
    """Group deleted assets by the storage action they require.

    Args:
        assets: assets deleted from the database.

    Returns:
        The assets grouped by action; assets requiring no action are omitted.
    """
    plan = StorageCleanupPlan(uploads_to_abort=[], directories_to_delete=[], files_to_delete=[])
    for asset in assets:
        if asset.status == AssetStatus.UPLOADING:
            # multipart uploads of a directory live on its child file assets
            if not asset.is_directory:
                plan.uploads_to_abort.append(asset)
        elif asset.parent_id is not None:
            # children are never deleted on their own: the parent's prefix delete covers them
            continue
        elif asset.is_directory:
            plan.directories_to_delete.append(asset)
        else:
            plan.files_to_delete.append(asset)
    return plan


def _abort_multipart_upload(asset: Asset, storage_client_factory: StorageClientFactory) -> None:
    try:
        # An asset should not have both UPLOADING status and None upload_meta
        assert asset.upload_meta is not None  # ruff:ignore[assert]
        multipart_upload_abort(
            upload_id=asset.upload_meta["upload_id"],
            storage_type=asset.storage_type,
            s3_key=asset.full_path,
            storage_client_factory=storage_client_factory,
        )
    except Exception:  # ruff:ignore[blind-except]
        L.exception(
            "Failed to abort multipart upload for Asset id={} full_path={} storage_type={}",
            asset.id,
            asset.full_path,
            asset.storage_type,
        )


def _abort_multipart_uploads(
    assets: list[Asset], storage_client_factory: StorageClientFactory
) -> None:
    # S3 has no batch abort API, so parallelize the per-upload calls
    if not assets:
        return
    max_workers = min(settings.S3_MAX_WORKERS, len(assets))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for asset in assets:
            executor.submit(_abort_multipart_upload, asset, storage_client_factory)


def _delete_directories(assets: list[Asset], storage_client_factory: StorageClientFactory) -> None:
    for asset in assets:
        try:
            delete_directory_storage_objects(
                storage_type=asset.storage_type,
                s3_prefix=asset.full_path,
                storage_client_factory=storage_client_factory,
            )
        except Exception:  # ruff:ignore[blind-except]
            L.exception(
                "Failed to delete storage directory for Asset id={} full_path={} storage_type={}",
                asset.id,
                asset.full_path,
                asset.storage_type,
            )


def _delete_files(assets: list[Asset], storage_client_factory: StorageClientFactory) -> None:
    keys_by_storage: defaultdict[StorageType, list[str]] = defaultdict(list)
    for asset in assets:
        keys_by_storage[asset.storage_type].append(asset.full_path)
    for storage_type, s3_keys in keys_by_storage.items():
        try:
            delete_storage_objects(
                storage_type=storage_type,
                s3_keys=s3_keys,
                storage_client_factory=storage_client_factory,
            )
        except Exception:  # ruff:ignore[blind-except]
            L.exception(
                "Failed to delete storage objects for {} asset(s) from storage {}",
                len(s3_keys),
                storage_type,
            )


@event.listens_for(Asset, "before_delete")
def collect_asset_for_storage_deletion(_mapper, _connection, target: Asset):
    """Collect Asset for S3 object cleanup after database deletion."""
    session = object_session(target)

    if session is not None:
        session.info.setdefault(ASSETS_TO_DELETE_KEY, set()).add(target)
    else:
        L.warning("Asset {} not attached to a session.", target.id)


@event.listens_for(Session, "after_commit")
def delete_assets_from_storage(session: Session):
    """Delete storage objects for assets removed in a committed transaction.

    Never raises: external failures are logged so the db assets stay deleted (possibly leaving s3
    orphans) rather than being resurrected by a rollback.

    See ``plan_storage_cleanup`` for how assets are routed. Directories are deleted by prefix,
    which also covers legacy directories whose files are not registered as child assets.

    No ``VersionId`` is passed, so versioning-enabled buckets keep a recoverable version behind a
    delete marker. A same-prefix re-upload racing this post-commit delete is practically
    unreachable: unique constraints forbid re-registering the path, and the directory asset is
    already gone.

    TODO: Add a cleanup function on a schedule that would remove s3 orphans from time to time.
    """
    assets: set[Asset] = session.info.pop(ASSETS_TO_DELETE_KEY, set())
    if not assets:
        return

    # Pre-instantiate one client per storage type so they can be reused across deletions.
    clients = {st: get_s3_client(storages[st]) for st in {asset.storage_type for asset in assets}}

    def storage_client_factory(storage):
        return clients[storage.type]

    plan = plan_storage_cleanup(assets)
    _abort_multipart_uploads(plan.uploads_to_abort, storage_client_factory)
    _delete_directories(plan.directories_to_delete, storage_client_factory)
    _delete_files(plan.files_to_delete, storage_client_factory)


@event.listens_for(Session, "after_rollback")
def cleanup_storage_deletes(session: Session):
    """Clear pending storage deletions after a transaction rollback."""
    session.info.pop(ASSETS_TO_DELETE_KEY, None)


STORAGE_UNDOS_KEY = "storage_writes_to_undo"


@dataclasses.dataclass(frozen=True)
class StorageUndo:
    """A write to take back: the S3 version it made.

    The bucket keeps old versions, so deleting ours makes the previous one current again.
    It never touches a newer write: if someone wrote after us, theirs stays current and ours
    just drops out of the history. One request, no bytes through the service.
    """

    storage_type: StorageType
    s3_key: str
    version_id: str
    transaction: SessionTransaction | None = None


def undo_storage_write_unless_committed(session: Session, undo: StorageUndo) -> None:
    """Restore the object if the current transaction doesn't commit.

    S3 can't roll back with the database, so we undo the write ourselves (a compensating
    action, saga pattern). This covers a rollback after an error, a failed commit, and a
    session closed without committing. The undo sits on the innermost transaction (the
    request's), and its commit drops it.

    Limit: a write made inside a savepoint is kept once the savepoint is released, even if an
    outer transaction rolls back later. No route writes to S3 inside a savepoint today.
    Upgrade: hand the undo to the parent transaction on release.
    """
    transaction = session.get_nested_transaction() or session.get_transaction()
    if transaction is None:
        # No transaction to wait for, so nothing can roll back the row either.
        return
    session.info.setdefault(STORAGE_UNDOS_KEY, []).append(
        dataclasses.replace(undo, transaction=transaction)
    )


def _undos_of(session: Session, transaction: SessionTransaction | None) -> list[StorageUndo]:
    """Remove and return the session's undos that belong to ``transaction``."""
    undos: list[StorageUndo] = session.info.get(STORAGE_UNDOS_KEY, [])
    mine = [u for u in undos if u.transaction is transaction]
    if mine:
        session.info[STORAGE_UNDOS_KEY] = [u for u in undos if u.transaction is not transaction]
    return mine


@event.listens_for(Session, "after_commit")
def keep_committed_storage_writes(session: Session):
    """The transaction committed, so its writes stay: drop their undos."""
    # The committing transaction is still the session's current one here.
    committed = session.get_nested_transaction() or session.get_transaction()
    _undos_of(session, committed)


@event.listens_for(Session, "after_transaction_end")
def undo_uncommitted_storage_writes(session: Session, transaction: SessionTransaction):
    """Take back the S3 writes of a transaction that ended without a commit.

    Never raises: a failed undo is just logged. The row then has the old version and the
    object the new one, until the asset is replaced again.
    """
    for undo in _undos_of(session, transaction):
        storage = storages[undo.storage_type]
        try:
            # Needs s3:DeleteObjectVersion, which the service's role has.
            get_s3_client(storage).delete_object(
                Bucket=storage.bucket, Key=undo.s3_key, VersionId=undo.version_id
            )
            L.warning("Took back s3 write {}: its transaction did not commit", undo.s3_key)
        except Exception:  # ruff:ignore[blind-except]
            L.exception("Failed to take back s3 write {}", undo.s3_key)
