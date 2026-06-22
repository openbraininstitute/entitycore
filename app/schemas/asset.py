import datetime
import uuid
from pathlib import Path
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BeforeValidator,
    Field,
    field_validator,
    model_validator,
)
from pydantic.networks import AnyUrl

from app.config import settings, storages
from app.db.types import (
    CONTENT_TYPE_TO_SUFFIX,
    AssetLabel,
    AssetStatus,
    ContentType,
    EntityType,
    LabelRequirements,
    StorageType,
)
from app.schemas.base import Schema


def validate_relative_path(path: Path) -> Path:
    """Validate a relative path.

    Any path is valid as long as it:
    - is not absolute
    - is not empty or "."
    - does not contain ".." components

    Leading "./" and trailing "/" are stripped away by pathlib.
    """
    if not path.parts:
        msg = "Empty paths are forbidden"
        raise ValueError(msg)
    if path.is_absolute():
        msg = "Absolute paths are forbidden"
        raise ValueError(msg)
    if ".." in path.parts:
        msg = "Parent traversal is forbidden"
        raise ValueError(msg)
    return path


def validate_path_component(path: Path) -> Path:
    """Validate a single path component (file or directory), not nested."""
    if len(path.parts) != 1 or path.parts[0] in {"..", "/"}:
        msg = "Expected a valid file or directory name"
        raise ValueError(msg)
    return path


def validate_relative_path_str(s: str) -> str:
    """Validate a relative path as a string."""
    if (normalized := str(validate_relative_path(Path(s)))) != s:
        msg = f"Path must be normalized as {normalized!r}"
        raise ValueError(msg)
    return s


def validate_path_component_str(s: str) -> str:
    """Validate a single path component (file or directory) as string, not nested."""
    if (normalized := str(validate_path_component(Path(s)))) != s:
        msg = f"Name must be normalized as {normalized!r}"
        raise ValueError(msg)
    return s


PathComponentStr = Annotated[str, AfterValidator(validate_path_component_str)]
RelativePathStr = Annotated[str, AfterValidator(validate_relative_path_str)]
Sha256Digest = Annotated[
    str,
    Field(
        description="SHA256 digest of the file content in hexadecimal format.",
        pattern=r"^[a-fA-F0-9]{64}$",
    ),
    BeforeValidator(lambda x: x.hex() if isinstance(x, bytes) else x),  # convert bytes from db
]


class AssetBase(Schema):
    """Asset model with common attributes."""

    path: RelativePathStr
    full_path: RelativePathStr
    is_directory: bool
    content_type: ContentType
    meta: dict = {}  # noqa: RUF012
    label: AssetLabel
    storage_type: StorageType


class SizeAndDigestMixin(Schema):
    """Mixin with size and digest."""

    size: int
    sha256_digest: Sha256Digest | None


class AssetRead(AssetBase, SizeAndDigestMixin):
    """Asset model for responses."""

    id: uuid.UUID
    status: AssetStatus


class ToUploadPart(Schema):
    part_number: Annotated[int, Field(description="Index of this part in the multipart upload.")]
    url: Annotated[str, Field(description="Presigned url to upload file part.")]


class UploadMeta(Schema):
    """Database schema."""

    upload_id: Annotated[str, Field(description="Unique ID for this multipart upload session.")]
    part_size: Annotated[int, Field(description="Size in bytes for each part.")]
    part_count: Annotated[int, Field(description="Total number of parts.")]


class UploadMetaRead(Schema):
    """Response schema."""

    parts: list[ToUploadPart]
    part_size: Annotated[int, Field(description="Size in bytes for each part.")]


class AssetReadWithUploadMeta(AssetRead):
    upload_meta: UploadMetaRead | None = None


class AssetCreate(AssetBase, SizeAndDigestMixin):
    """Asset model for creation."""

    entity_type: EntityType
    parent_id: uuid.UUID | None
    created_by_id: uuid.UUID
    updated_by_id: uuid.UUID

    @model_validator(mode="after")
    def ensure_parent_id_consistency(self):
        """Ensure consistency of parent_id."""
        if self.is_directory is True and self.parent_id is not None:
            msg = "Directories assets cannot have a parent_id"
            raise ValueError(msg)
        return self


def validate_asset_label(
    asset: AssetCreate,
    allowed_labels: dict[AssetLabel, list[LabelRequirements]] | None,
) -> None:
    """Validate an asset label and its requirements against an allowed-label map."""
    if allowed_labels is None:
        msg = f"There are no allowed asset labels defined for '{asset.entity_type}'"
        raise ValueError(msg)

    if asset.label == AssetLabel.directory_child:
        if asset.parent_id is None:
            msg = "Directory child assets must have a parent_id"
            raise ValueError(msg)
        return

    if asset.label not in allowed_labels:
        msg = (
            f"Asset label '{asset.label}' is not allowed for entity type '{asset.entity_type}'. "
            f"Allowed asset labels: {sorted(label.value for label in allowed_labels)}"
        )
        raise ValueError(msg)

    _raise_on_label_requirement(asset, allowed_labels[asset.label])


def _raise_on_label_requirement(asset: AssetBase, label_reqs: list[LabelRequirements]) -> None:
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


class AssetRegister(AssetBase):
    """Asset model for registration of assets already in cloud."""

    @field_validator("storage_type", mode="after")
    @classmethod
    def validate_storage_type_is_open(cls, v: StorageType) -> StorageType:
        if not storages[v].is_open:
            msg = "Only open data storage is supported for registration"
            raise ValueError(msg)
        return v


class AssetsMixin:
    assets: list[AssetRead]


class DirectoryUploadRequest(Schema):
    directory_name: Annotated[
        PathComponentStr,
        Field(
            description="Name of the directory to be uploaded. Nested directories aren't allowed.",
            min_length=1,
        ),
    ]
    files: Annotated[
        list[RelativePathStr],
        Field(
            description="List of filenames to be uploaded, relative to the base directory.",
            min_length=1,
        ),
    ]
    meta: dict | None = None
    label: AssetLabel

    @model_validator(mode="after")
    def verify_children(self):
        """Verify the validity of the children."""
        unique_filenames = set(self.files)
        if len(unique_filenames) != len(self.files):
            msg = "Filenames must be unique within the directory."
            raise ValueError(msg)
        return self


class DetailedFile(Schema):
    name: str
    size: int
    last_modified: datetime.datetime


class DetailedFileList(Schema):
    files: dict[Path, DetailedFile]


class AssetAndPresignedURLS(Schema):
    asset: AssetRead
    files: dict[Path, AnyUrl]


class MultipartUploadInitiateRequest(Schema):
    filename: Annotated[
        PathComponentStr,
        Field(description="File name to be uploaded."),
    ]
    filesize: Annotated[
        int,
        Field(
            description="File size to be uploaded in bytes.",
            gt=0,
            lt=settings.S3_MULTIPART_UPLOAD_MAX_SIZE,
        ),
    ]
    sha256_digest: Sha256Digest
    content_type: Annotated[
        ContentType | None,
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


class MultipartDirectoryFileRequest(Schema):
    filename: Annotated[
        RelativePathStr,
        Field(description="File name to be uploaded, relative to the base directory."),
    ]
    filesize: Annotated[
        int,
        Field(
            description="File size to be uploaded in bytes.",
            ge=0,
            lt=settings.S3_MULTIPART_UPLOAD_MAX_SIZE,
        ),
    ]
    sha256_digest: Sha256Digest
    content_type: Annotated[
        ContentType | None,
        Field(
            description=(
                "Content type of file. "
                "If not provided it will be deduced from the file's extension."
            )
        ),
    ] = None
    label: Literal[AssetLabel.directory_child] = AssetLabel.directory_child
    preferred_part_count: Annotated[int, Field(description="Hint of desired part count.")] = (
        settings.S3_MULTIPART_UPLOAD_DEFAULT_PARTS
    )


class MultipartDirectoryUploadRequest(Schema):
    """Request schema for initiating a multipart directory upload.

    Similar to DirectoryUploadRequest schema, but with additional information for multipart uploads.
    """

    directory_name: Annotated[
        PathComponentStr,
        Field(
            description="Name of the directory to be uploaded. Nested directories are not allowed.",
        ),
    ]
    files: Annotated[
        list[MultipartDirectoryFileRequest],
        Field(
            description="List of files to be uploaded inside the directory.",
            min_length=1,
        ),
    ]
    meta: dict | None = None
    label: AssetLabel

    @model_validator(mode="after")
    def verify_children(self):
        """Verify the validity of the children."""
        unique_filenames = {file.filename for file in self.files}
        if len(unique_filenames) != len(self.files):
            msg = "Filenames must be unique within the directory."
            raise ValueError(msg)
        return self


class MultipartDirectoryUploadResponse(Schema):
    """Response schema after initiating a multipart directory upload.

    Similar to AssetAndPresignedURLS schema, but with additional information for multipart uploads.
    """

    asset: AssetRead
    files: list[AssetReadWithUploadMeta]
