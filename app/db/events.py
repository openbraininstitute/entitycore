from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import object_session

from app.db.model import Asset
from app.db.types import AssetStatus
from app.logger import L
from app.utils.s3 import delete_asset_storage_object, get_s3_client, multipart_upload_abort

ASSETS_TO_DELETE_KEY = "assets_to_delete_from_storage"


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

    Note: Due to the nature of the operation that iterates over all assets it is important to not
    throw an error even if one of the external side-effect fail. Otherwise, after the rollback
    there might be db assets that are not deleted but their s3 files are.

    Instead with capturing the errors it is ensured that db assets are always deleted even if that
    may result in orphan files or multipart uploads that have failed to be deleted.

    TODO: Add a cleanup function on a schedule that would remove s3 orphans from time to time.
    """
    to_delete: set[Asset] = session.info.pop(ASSETS_TO_DELETE_KEY, set())
    for asset in to_delete:
        match asset.status:
            case AssetStatus.UPLOADING:
                try:
                    # An asset should not have both UPLOADING status and None upload_meta
                    assert asset.upload_meta is not None  # noqa: S101
                    multipart_upload_abort(
                        upload_id=asset.upload_meta["upload_id"],
                        storage_type=asset.storage_type,
                        s3_key=asset.full_path,
                        storage_client_factory=get_s3_client,
                    )
                except Exception:  # noqa: BLE001
                    L.exception(
                        (
                            "Failed to abort multipart upload for Asset "
                            "id={} full_path={} storage_type={}"
                        ),
                        asset.id,
                        asset.full_path,
                        asset.storage_type,
                    )
            case _:
                try:
                    delete_asset_storage_object(
                        storage_type=asset.storage_type,
                        s3_key=asset.full_path,
                        storage_client_factory=get_s3_client,
                    )
                except Exception:  # noqa: BLE001
                    L.exception(
                        (
                            "Failed to delete storage object for Asset "
                            "id={} full_path={} storage_type={}"
                        ),
                        asset.id,
                        asset.full_path,
                        asset.storage_type,
                    )


@event.listens_for(Session, "after_rollback")
def cleanup_storage_deletes(session: Session):
    """Clear pending storage deletions after a transaction rollback."""
    session.info.pop(ASSETS_TO_DELETE_KEY, None)
