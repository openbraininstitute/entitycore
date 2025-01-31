from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.types import AssetStatus


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Annotated[UUID, Field(alias="uuid")]
    path: str
    status: AssetStatus
    meta: dict
