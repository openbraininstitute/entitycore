import uuid

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.db.types import ALLOWED_ASSET_LABELS_PER_ENTITY, AssetLabel, AssetStatus, EntityType


class AssetBase(BaseModel):
    """Asset model with common attributes."""

    model_config = ConfigDict(from_attributes=True)
    path: str
    full_path: str
    is_directory: bool
    content_type: str
    size: int
    sha256_digest: str | None
    meta: dict
    label: AssetLabel | None = None

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

    entity_type: EntityType

    @model_validator(mode="after")
    def ensure_entity_type_label_consistency(self):
        """Asset label must be within the allowed labels for the entity_type."""
        if not self.label:
            return self

        allowed_asset_labels = ALLOWED_ASSET_LABELS_PER_ENTITY.get(self.entity_type, None)

        if allowed_asset_labels is None:
            msg = f"There are no allowed asset labels defined for '{self.entity_type}'"
            raise ValueError(msg)

        if self.label not in allowed_asset_labels:
            msg = (
                f"Asset label '{self.label}' is not allowed for entity type '{self.entity_type}'. "
                f"Allowed asset labels: {sorted(label.value for label in allowed_asset_labels)}"
            )
            raise ValueError(msg)

        return self


class AssetsMixin(BaseModel):
    assets: list[AssetRead]
