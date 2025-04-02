import uuid

from pydantic import BaseModel, ConfigDict, field_validator

from app.db.types import AssetStatus


class AssetBase(BaseModel):
    """Asset model with common attributes."""

    model_config = ConfigDict(from_attributes=True)
    path: str
    full_path: str
    bucket_name: str
    is_directory: bool
    content_type: str
    size: int
    sha256_digest: str | None
    meta: dict

    @field_validator("sha256_digest", mode="before")
    @classmethod
    def convert_bytes_to_hex(cls, value: bytes | str | None) -> str | None:
        if isinstance(value, bytes):
            return value.hex()
        return value  # fallback (str or None)


class AssetRead(AssetBase):
    """Asset model for responses."""

    id: uuid.UUID
    status: AssetStatus


class AssetCreate(AssetBase):
    """Asset model for creation."""


class AssetsMixin(BaseModel):
    assets: list[AssetRead] | None
