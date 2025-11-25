from sqlalchemy import event

from app.db.model import Asset
from app.service.asset import delete_asset_storage_object
from app.utils.s3 import get_s3_client


@event.listens_for(Asset, "after_delete")
def delete_asset_storage_object_event(_mapper, _connection, target):
    """Trigger s3 file/directory deletion after an Asset is deleted."""
    delete_asset_storage_object(asset=target, storage_client_factory=get_s3_client)
