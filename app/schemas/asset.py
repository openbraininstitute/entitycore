import datetime
import uuid
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic.networks import AnyUrl

from app.db.types import (
    ALLOWED_ASSET_LABELS_PER_ENTITY,
    CONTENT_TYPE_TO_SUFFIX,
    AssetLabel,
    AssetStatus,
    ContentType,
    EntityType,
)


class AssetBase(BaseModel):
    """Asset model with common attributes."""

    model_config = ConfigDict(from_attributes=True)
    path: str
    full_path: str
    is_directory: bool
    content_type: ContentType
    size: int
    sha256_digest: str | None
    meta: dict
    label: AssetLabel

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


def _raise_on_label_requirement(asset, label_reqs):
    content_type_success = [
        label_req.content_type == asset.content_type
        for label_req in label_reqs
        if label_req.content_type and not label_req.is_directory
    ]
    if content_type_success and not any(content_type_success):
        allowed_content_types = {
            label_req.content_type for label_req in label_reqs if label_req.content_type
        }
        msg = f"{asset.label} implies the should be on one of the following content-types: {allowed_content_types}"
        raise ValueError(msg)

    directory_errors = []
    suffix_errors = []
    for req in label_reqs:
        if req.is_directory != asset.is_directory:
            directory_errors.append(
                "The label requirement for directory does not match `is_directory`"
            )

        suffix = Path(asset.path).suffix.lower()
        if (
            req.content_type
            and req.content_type == asset.content_type
            and not any(s == suffix for s in CONTENT_TYPE_TO_SUFFIX[req.content_type])
        ):
            suffix_errors.append(f"Suffix for content-type {CONTENT_TYPE_TO_SUFFIX[req.content_type]} does not match {suffix}")

    if directory_errors:
        raise ValueError("\n".join(suffix_errors))
    if suffix_errors:
        raise ValueError("\n".join(suffix_errors))


class AssetCreate(AssetBase):
    """Asset model for creation."""

    entity_type: EntityType
    created_by_id: uuid.UUID
    updated_by_id: uuid.UUID

    @model_validator(mode="after")
    def ensure_entity_type_label_consistency(self):
        """Asset label must be within the allowed labels for the entity_type."""
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

        _raise_on_label_requirement(self, allowed_asset_labels[self.label])

        return self


class AssetsMixin(BaseModel):
    assets: list[AssetRead]


class DirectoryUpload(BaseModel):
    directory_name: Path
    files: list[Path]
    meta: dict | None
    label: AssetLabel


class DetailedFile(BaseModel):
    name: str
    size: int
    last_modified: datetime.datetime


class DetailedFileList(BaseModel):
    files: dict[Path, DetailedFile]


class AssetAndPresignedURLS(BaseModel):
    asset: AssetRead
    files: dict[Path, AnyUrl]
