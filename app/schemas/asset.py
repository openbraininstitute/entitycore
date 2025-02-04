from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.types import AssetStatus


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid: UUID
    status: AssetStatus
    fullpath: str
    path: str
    is_directory: bool
    content_type: str
    size: int
    meta: dict
