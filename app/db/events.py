from sqlalchemy import event
from sqlalchemy.orm import Session

from app.db.model import Asset
from app.logger import L
from app.service.asset import delete_asset_storage_object
from app.utils.s3 import get_s3_client

ASSETS_TO_DELETE_KEY = "assets_to_delete_from_storage"


@event.listens_for(Session, "after_flush")
def collect_assets_for_storage_delete(session: Session, _):
    """Collect hard-deleted Asset instances for post-commit storage cleanup."""
    to_delete = session.info.setdefault(ASSETS_TO_DELETE_KEY, [])
    to_delete.extend(obj for obj in session.deleted if isinstance(obj, Asset))


@event.listens_for(Session, "after_commit")
def delete_assets_from_storage(session: Session):
    """Delete storage objects for assets removed in a committed transaction."""
    to_delete = session.info.pop(ASSETS_TO_DELETE_KEY, [])

    for asset in to_delete:
        try:
            delete_asset_storage_object(
                asset=asset,
                storage_client_factory=get_s3_client,
            )
        except Exception as e:  # noqa: BLE001
            L.error(
                "Failed to delete storage object for Asset id=%s full_path=%s storage_type=%s",
                asset.id,
                asset.full_path,
                asset.storage_type,
                exc_info=e,
            )


@event.listens_for(Session, "after_rollback")
def cleanup_storage_deletes(session: Session):
    """Clear pending storage deletions after a transaction rollback."""
    session.info.pop(ASSETS_TO_DELETE_KEY, None)
