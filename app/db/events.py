from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import object_session

from app.db.model import Asset
from app.logger import L
from app.utils.s3 import delete_asset_storage_object, get_s3_client

ASSETS_TO_DELETE_KEY = "assets_to_delete_from_storage"


@event.listens_for(Asset, "before_delete")
def asset_before_delete(_mapper, _connection, target: Asset):
    session = object_session(target)

    if session is not None:
        session.info.setdefault(ASSETS_TO_DELETE_KEY, set()).add(target)
    else:
        L.warning("Asset {} not attached to a session.", target.id)


@event.listens_for(Session, "after_commit")
def delete_assets_from_storage(session: Session):
    """Delete storage objects for assets removed in a committed transaction."""
    to_delete = session.info.pop(ASSETS_TO_DELETE_KEY, set())
    for asset in to_delete:
        try:
            delete_asset_storage_object(
                storage_type=asset.storage_type,
                s3_key=asset.full_path,
                storage_client_factory=get_s3_client,
            )
        except Exception as e:  # noqa: BLE001
            L.exception(
                "Failed to delete storage object for Asset id={} full_path={} storage_type={}",
                asset.id,
                asset.full_path,
                asset.storage_type,
                exc_info=e,
            )


@event.listens_for(Session, "after_rollback")
def cleanup_storage_deletes(session: Session):
    """Clear pending storage deletions after a transaction rollback."""
    session.info.pop(ASSETS_TO_DELETE_KEY, None)
