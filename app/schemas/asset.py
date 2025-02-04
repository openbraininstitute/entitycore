from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.types import AssetStatus


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID
    path: str
    status: AssetStatus
    meta: dict
