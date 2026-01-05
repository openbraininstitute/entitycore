import datetime
import uuid
from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.networks import AnyUrl

from app.config import settings, storages
from app.db.types import (
    ALLOWED_ASSET_LABELS_PER_ENTITY,
    CONTENT_TYPE_TO_SUFFIX,
    AssetLabel,
    AssetStatus,
    ContentType,
    EntityType,
    StorageType,
)


def validate_path(s: str) -> str:
    if s in {"", ".", ".."} or "/" in s:
        msg = "Invalid path: cannot be empty, '.', '..', or contain '/'"
        raise ValueError(msg)
    return s


def validate_full_path(s: str) -> str:
    forbidden = {"", ".", ".."}
    items = s.split("/")
    # even directories are not allowed to start or end with '/'
    if not items or any(item in forbidden for item in items):
        msg = (
            "Invalid full path: cannot be empty, start or end with '/', "
            "and the path components cannot be empty, '.' or '..'"
        )
        raise ValueError(msg)
    return s


class ToUploadPart(BaseModel):
    part_number: int
    url: Annotated[str, Field(description="Presigned url to upload file part.")]


class UploadMeta(BaseModel):
    upload_id: str
    part_size: int
    parts: list[ToUploadPart]


class AssetBase(BaseModel):
    """Asset model with common attributes."""

    model_config = ConfigDict(from_attributes=True)
    path: Annotated[str, AfterValidator(validate_path)]
    full_path: Annotated[str, AfterValidator(validate_full_path)]
    is_directory: bool
    content_type: ContentType
    meta: dict = {}
    label: AssetLabel
    storage_type: StorageType
    upload_meta: UploadMeta | None = None


class SizeAndDigestMixin(BaseModel):
    """Mixin with size and digest."""

    size: int
    sha256_digest: str | None

    @field_validator("sha256_digest", mode="before")
    @classmethod
    def convert_bytes_to_hex(cls, value: bytes | str | None) -> str | None:
        if isinstance(value, bytes):
            return value.hex()
        return value  # fallback (str or None)


class AssetRead(AssetBase, SizeAndDigestMixin):
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
        allowed_content_types = sorted(
            label_req.content_type.value for label_req in label_reqs if label_req.content_type
        )
        msg = f"{asset.label} implies one of the following content-types: {allowed_content_types}"
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
            and suffix not in CONTENT_TYPE_TO_SUFFIX[req.content_type]
        ):
            suffix_errors.append(
                f"Suffix for content-type {CONTENT_TYPE_TO_SUFFIX[req.content_type]} "
                f"does not match {suffix}"
            )

    if directory_errors:
        raise ValueError(directory_errors[0])

    if suffix_errors:
        raise ValueError(suffix_errors[0])


class AssetCreate(AssetBase, SizeAndDigestMixin):
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


class AssetRegister(AssetBase):
    """Asset model for registration of assets already in cloud."""

    @field_validator("storage_type", mode="after")
    @classmethod
    def validate_storage_type_is_open(cls, v: StorageType) -> StorageType:
        if not storages[v].is_open:
            msg = "Only open data storage is supported for registration"
            raise ValueError(msg)
        return v


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


class InitiateUploadRequest(BaseModel):
    filename: Annotated[str, Field(description="File name to be uploaded.")]
    filesize: Annotated[int, Field(description="File size to be uploaded in bytes.")]
    sha256_digest: str
    content_type: Annotated[
        str | None,
        Field(
            description=(
                "Content type of file. "
                "If not provided it will be deduced from the file's extension."
            )
        ),
    ] = None
    label: AssetLabel
    preferred_part_count: Annotated[int, Field(description="Hint of desired part count.")] = (
        settings.S3_MULTIPART_UPLOAD_DEFAULT_PARTS
    )


class UploadedPart(BaseModel):
    part_number: int
    etag: str
