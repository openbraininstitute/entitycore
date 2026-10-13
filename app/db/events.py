from collections import defaultdict
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import NamedTuple

from sqlalchemy import event
from sqlalchemy.orm import Session
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
