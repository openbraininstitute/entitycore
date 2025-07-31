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
from types_boto3_s3 import S3Client
from types_boto3_s3.type_defs import PaginatorConfigTypeDef

from app.config import StorageUnion, settings
from app.db.types import EntityType
from app.logger import L
from app.schemas.asset import validate_path


class StorageClientFactory(Protocol):
    def __call__(self, storage: StorageUnion) -> S3Client: ...


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
    prefix = "public" if is_public else "private"
    return f"{prefix}/{vlab_id}/{proj_id}/assets/{entity_type.name}/{entity_id}/{filename}"


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
    config = TransferConfig(multipart_threshold=settings.S3_MULTIPART_THRESHOLD)
    try:
        s3_client.upload_fileobj(
            file_obj,
            Bucket=bucket_name,
            Key=s3_key,
            Config=config,
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


def list_directory_with_details(
    s3_client: S3Client,
    bucket_name: str,
    prefix: str,
    pagination_config: PaginatorConfigTypeDef | None = None,
) -> dict:
    # with `prefix="foo/asdf" argument will match all `foo/asdf/` and `foo/asdf_asdf/,
    # insure we have a ending / to prevent being promiscuous
    if not prefix.endswith("/"):
        prefix += "/"

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
