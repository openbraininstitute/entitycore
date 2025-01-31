from pydantic import BaseModel, ConfigDict

from app.db.types import AssetStatus


class AssetBase(BaseModel):
    """Asset model with common attributes."""

    model_config = ConfigDict(from_attributes=True)
    path: str
    fullpath: str
    bucket_name: str
    is_directory: bool
    content_type: str
    size: int
    meta: dict


class AssetRead(AssetBase):
    """Asset model for responses."""

    id: int
    status: AssetStatus


class AssetCreate(AssetBase):
    """Asset model for creation."""
