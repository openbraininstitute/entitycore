import math
import os
import uuid
from pathlib import Path
from typing import IO, Protocol
from urllib.parse import urlparse, urlunparse
from uuid import UUID

import boto3
import botocore.client
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
from fastapi import HTTPException
from types_boto3_s3 import S3Client
from types_boto3_s3.type_defs import (
    CopySourceTypeDef,
    DeleteObjectRequestTypeDef,
    PaginatorConfigTypeDef,
)

from app.config import StorageUnion, settings, storages
from app.db.types import EntityType, StorageType
from app.logger import L
from app.schemas.asset import validate_path
from app.schemas.publish import MoveDirectoryResult, MoveFileResult
from app.utils.common import clip

PUBLIC_ASSET_PREFIX = "public/"
PRIVATE_ASSET_PREFIX = "private/"


class StorageClientFactory(Protocol):
    def __call__(self, storage: StorageUnion) -> S3Client: ...


def ensure_directory_prefix(prefix: str) -> str:
    """Return the prefix with a trailing '/' if it's missing."""
    if not prefix.endswith("/"):
        prefix += "/"
    return prefix


def get_s3_path_prefix(*, public: bool) -> str:
    """Return the S3 path prefix for public or private assets."""
    return PUBLIC_ASSET_PREFIX if public else PRIVATE_ASSET_PREFIX


def build_s3_path(
    *,
    vlab_id: UUID,
    proj_id: UUID,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    filename: str | os.PathLike,
    is_public: bool,
) -> str:
    """Return the key used to store the file on S3."""
    prefix = get_s3_path_prefix(public=is_public)
    return f"{prefix}{vlab_id}/{proj_id}/assets/{entity_type.name}/{entity_id}/{filename}"


def convert_s3_path_visibility(s3_path: str, *, public: bool) -> str:
    """Convert a private S3 path to a public one, or vice versa.

    Args:
        s3_path: the original S3 path.
        public: whether the returned path should be public or private.
    """
    old_prefix = get_s3_path_prefix(public=not public)
    new_prefix = get_s3_path_prefix(public=public)
    if not s3_path.startswith(old_prefix):
        msg = f"S3 path must start with {old_prefix!r}."
        raise ValueError(msg)
    return new_prefix + s3_path.removeprefix(old_prefix)


def validate_filename(filename: str) -> bool:
    try:
        validate_path(filename)
    except ValueError:
        return False
    return True


def sanitize_directory_traversal(filename: str | Path) -> Path:
    return Path(os.path.normpath("/" / Path(filename))).relative_to("/")


def validate_filesize(filesize: int) -> bool:
    return filesize <= settings.API_ASSET_POST_MAX_SIZE


def validate_multipart_filesize(filesize: int) -> bool:
    return filesize <= settings.S3_MULTIPART_UPLOAD_MAX_SIZE


def get_s3_client(storage: StorageUnion) -> S3Client:
    """Return a new S3 client (not thread-safe).

    Boto should get credentials from ~/.aws/credentials or the environment.
    In particular, the following keys are required:

    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_ENDPOINT_URL

    Implements StorageClientFactory.

    Args:
        storage: Storage configuration.
    """
    if storage.is_open:
        # For open storage, we use unsigned requests
        config = botocore.client.Config(signature_version=botocore.UNSIGNED)
    else:
        # For internal storage, we use signed requests
        config = botocore.client.Config()
    return boto3.client("s3", region_name=storage.region, config=config)


def upload_to_s3(
    s3_client: S3Client,
    file_obj: IO,
    bucket_name: str,
    s3_key: str,
) -> bool:
    """Upload an object to an S3 bucket.

    Args:
        s3_client: S3 client instance.
        file_obj: file-like object.
        bucket_name: name of the S3 bucket.
        s3_key: S3 object key (destination path in the bucket).
    """
    try:
        s3_client.upload_fileobj(
            file_obj,
            Bucket=bucket_name,
            Key=s3_key,
            Config=TransferConfig(
                multipart_threshold=settings.S3_MULTIPART_UPLOAD_THRESHOLD,
                multipart_chunksize=settings.S3_MULTIPART_UPLOAD_CHUNKSIZE,
            ),
        )
    except Exception:  # noqa: BLE001
        L.exception("Error while uploading file to s3://{}/{}", bucket_name, s3_key)
        return False
    L.info("File uploaded successfully to s3://{}/{}", bucket_name, s3_key)
    return True


def delete_from_s3(s3_client: S3Client, bucket_name: str, s3_key: str) -> bool:
    """Delete an object from an S3 bucket.

    Args:
        s3_client: S3 client instance.
        bucket_name: name of the S3 bucket.
        s3_key: S3 object key (file path in the bucket).
    """
    try:
        response = s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
    except Exception:  # noqa: BLE001
        L.exception("Error while deleting file from s3://{}/{}", bucket_name, s3_key)
        return False
    # if using versioning-enabled buckets, we could store the version id for recovery
    version_id = response.get("VersionId")
    L.info(
        "File deleted successfully from s3://{}/{}?versionId={}", bucket_name, s3_key, version_id
    )
    return True


def delete_asset_storage_object(
    *, storage_type: StorageType, s3_key: str, storage_client_factory: StorageClientFactory
):
    """Delete asset storage object."""
    # TODO: Handle directories. See https://github.com/openbraininstitute/entitycore/issues/256
    storage = storages[storage_type]
    # delete the file from S3 only if not using an open data storage
    if not storage.is_open:
        s3_client = storage_client_factory(storage)
        if not delete_from_s3(s3_client, bucket_name=storage.bucket, s3_key=s3_key):
            raise HTTPException(status_code=500, detail="Failed to delete object")


def generate_presigned_url(
    s3_client: S3Client, operation: str, bucket_name: str, s3_key: str
) -> str | None:
    """Generate and return a presigned URL for an S3 object.

    Args:
        s3_client: S3 client instance.
        operation: the `ClientMethod` wanted of the presigned url
        bucket_name: name of the S3 bucket.
        s3_key: S3 object key (destination path in the bucket).
    """
    url = None
    try:
        url = s3_client.generate_presigned_url(
            operation,
            Params={"Bucket": bucket_name, "Key": s3_key},
            ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRATION,
        )
        if settings.S3_PRESIGNED_URL_NETLOC:
            parsed = urlparse(url)
            url = urlunparse(parsed._replace(netloc=settings.S3_PRESIGNED_URL_NETLOC))
    except Exception:  # noqa: BLE001
        L.exception("Error generating presigned URL for s3://{}/{}", bucket_name, s3_key)
    return url


def multipart_upload_initiate(
    s3_client: S3Client, bucket: str, s3_key: str, content_type: str
) -> str:
    res = s3_client.create_multipart_upload(Bucket=bucket, Key=s3_key, ContentType=content_type)
    return res["UploadId"]


def multipart_compute_upload_plan(*, filesize: int, preferred_part_count: int) -> tuple[int, int]:
    part_count = clip(
        preferred_part_count,
        min_value=settings.S3_MULTIPART_UPLOAD_MIN_PARTS,
        max_value=settings.S3_MULTIPART_UPLOAD_MAX_PARTS,
    )
    part_size = math.ceil(filesize / part_count)

    part_size = clip(
        part_size,
        min_value=settings.S3_MULTIPART_UPLOAD_MIN_PART_SIZE,
        max_value=settings.S3_MULTIPART_UPLOAD_MAX_PART_SIZE,
    )
    part_count = math.ceil(filesize / part_size)

    return part_size, part_count


def multipart_upload_create_part_presigned_url(
    s3_client: S3Client,
    bucket: str,
    s3_key: str,
    upload_id: str,
    part_number: int,
):
    return s3_client.generate_presigned_url(
        "upload_part",
        Params={
            "Bucket": bucket,
            "Key": s3_key,
            "UploadId": upload_id,
            "PartNumber": part_number,
        },
        ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRATION,
    )


def multipart_upload_list_parts(
    s3_client: S3Client,
    bucket: str,
    s3_key: str,
    upload_id: str,
) -> list:
    paginator = s3_client.get_paginator("list_parts")
    page_iterator = paginator.paginate(
        Bucket=bucket,
        Key=s3_key,
        UploadId=upload_id,
    )
    return [part for page in page_iterator for part in page.get("Parts", [])]


def multipart_upload_complete(
    s3_client: S3Client, s3_key: str, upload_id: str, bucket: str, parts: list
):
    s3_client.complete_multipart_upload(
        Bucket=bucket,
        Key=s3_key,
        UploadId=upload_id,
        MultipartUpload={
            "Parts": [
                {
                    "ETag": p["ETag"],
                    "PartNumber": p["PartNumber"],
                }
                for p in parts
            ],
        },
    )


def multipart_upload_abort(
    *,
    upload_id: str,
    storage_type: StorageType,
    s3_key: str,
    storage_client_factory: StorageClientFactory,
) -> None:
    storage = storages[storage_type]
    s3_client = storage_client_factory(storage)
    s3_client.abort_multipart_upload(
        Bucket=storage.bucket,
        Key=s3_key,
        UploadId=upload_id,
    )


def list_directory_with_details(
    s3_client: S3Client,
    bucket_name: str,
    prefix: str,
    pagination_config: PaginatorConfigTypeDef | None = None,
) -> dict:
    # with `prefix="foo/asdf" argument will match all `foo/asdf/` and `foo/asdf_asdf/,
    # ensure we have a ending / to prevent being promiscuous
    prefix = ensure_directory_prefix(prefix)

    paginator = s3_client.get_paginator("list_objects_v2")
    files = {}
    for page in paginator.paginate(
        Bucket=bucket_name,
        Prefix=prefix,
        PaginationConfig=pagination_config or {},
    ):
        if "Contents" not in page:
            continue
        for obj in page["Contents"]:
            assert "Key" in obj and "Size" in obj and "LastModified" in obj  # noqa: PT018, S101
            name = str(Path(obj["Key"]).relative_to(prefix))
            files[name] = {
                "name": name,
                "size": obj["Size"],
                "last_modified": obj["LastModified"],
            }
    return files


def check_object(
    s3_client: S3Client,
    *,
    bucket_name: str,
    s3_key: str,
    is_directory: bool,
) -> dict:
    """Check if an object exists in S3 and return its type."""
    try:
        if is_directory:
            list_directory_with_details(
                s3_client,
                bucket_name=bucket_name,
                prefix=s3_key,
                pagination_config={"MaxItems": 1, "PageSize": 1},
            )
            object_type = "directory"
        else:
            s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            object_type = "file"
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in {"404", "403"}:
            # 404 = Not Found, 403 = Access Denied
            return {"exists": False}
        raise
    return {"exists": True, "type": object_type}


def copy_file(
    s3_client: S3Client,
    *,
    src_bucket_name: str,
    dst_bucket_name: str,
    src_key: str,
    dst_key: str,
) -> bool:
    """Copy a file in S3, using multipart copy for large objects.

    See https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/copy.html
    """
    copy_source: CopySourceTypeDef = {
        "Bucket": src_bucket_name,
        "Key": src_key,
    }
    try:
        s3_client.copy(
            CopySource=copy_source,
            Bucket=dst_bucket_name,
            Key=dst_key,
            Config=TransferConfig(
                multipart_threshold=settings.S3_MULTIPART_COPY_THRESHOLD,
                multipart_chunksize=settings.S3_MULTIPART_COPY_CHUNKSIZE,
            ),
        )
    except Exception:  # noqa: BLE001
        L.exception(
            "Error while copying file from s3://{}/{} to s3://{}/{}",
            src_bucket_name,
            src_key,
            dst_bucket_name,
            dst_key,
        )
        return False
    return True


def move_file(
    s3_client: S3Client,
    *,
    src_bucket_name: str,
    dst_bucket_name: str,
    src_key: str,
    dst_key: str,
    size: int,
    dry_run: bool,
) -> MoveFileResult:
    """Move a file in S3 by copying it to the new location and deleting the original."""
    if (src_bucket_name, src_key) == (dst_bucket_name, dst_key):
        msg = "Source and destination cannot be the same."
        raise ValueError(msg)
    if dry_run:
        return MoveFileResult(size=size, error=None)
    try:
        # check if the source object exists and get its metadata
        src_head = s3_client.head_object(Bucket=src_bucket_name, Key=src_key)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") != "404":
            raise
        try:
            # check if the destination object already exists
            s3_client.head_object(Bucket=dst_bucket_name, Key=dst_key)
        except ClientError:
            msg = f"Failed to get object s3://{src_bucket_name}/{src_key}"
            L.warning(msg)
            return MoveFileResult(size=size, error=msg)
        L.warning("Source already moved: s3://{}/{}", src_bucket_name, src_key)
        return MoveFileResult(size=size, error=None)
    if not copy_file(
        s3_client,
        src_bucket_name=src_bucket_name,
        dst_bucket_name=dst_bucket_name,
        src_key=src_key,
        dst_key=dst_key,
    ):
        msg = (
            f"Failed to copy object from s3://{src_bucket_name}/{src_key} "
            f"to s3://{dst_bucket_name}/{dst_key}"
        )
        L.warning(msg)
        return MoveFileResult(size=size, error=msg)
    # delete the original object without leaving a delete marker when versioning is enabled
    delete_kwargs: DeleteObjectRequestTypeDef = {"Bucket": src_bucket_name, "Key": src_key}
    if src_version_id := src_head.get("VersionId"):
        delete_kwargs["VersionId"] = src_version_id
    s3_client.delete_object(**delete_kwargs)
    return MoveFileResult(size=size, error=None)


def move_directory(
    s3_client: S3Client,
    *,
    src_bucket_name: str,
    dst_bucket_name: str,
    src_key: str,
    dst_key: str,
    dry_run: bool,
) -> MoveDirectoryResult:
    """Move a directory in S3 by copying it to the new location and deleting the original."""
    src_key = ensure_directory_prefix(src_key)
    dst_key = ensure_directory_prefix(dst_key)
    objects = list_directory_with_details(s3_client, bucket_name=src_bucket_name, prefix=src_key)
    move_directory_result = MoveDirectoryResult(size=0, file_count=0)
    for obj in objects.values():
        move_file_result = move_file(
            s3_client,
            src_bucket_name=src_bucket_name,
            dst_bucket_name=dst_bucket_name,
            src_key=f"{src_key}{obj['name']}",
            dst_key=f"{dst_key}{obj['name']}",
            size=obj["size"],
            dry_run=dry_run,
        )
        move_directory_result.update_from_file_result(move_file_result)
    return move_directory_result
