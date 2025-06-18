import os
import uuid
from pathlib import Path
from typing import IO
from urllib.parse import urlparse, urlunparse
from uuid import UUID

import boto3
from boto3.s3.transfer import TransferConfig
from types_boto3_s3 import S3Client

from app.config import settings
from app.db.types import EntityType
from app.logger import L


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
    # TODO: verify if prefix partitioning is needed for better performance
    return f"{prefix}/{vlab_id}/{proj_id}/assets/{entity_type.name}/{entity_id}/{filename}"


def validate_filename(filename: str) -> bool:
    return "/" not in filename


def sanitize_directory_traversal(filename: str | Path) -> Path:
    return Path(os.path.normpath("/" / Path(filename))).relative_to("/")


def validate_filesize(filesize: int) -> bool:
    return filesize <= settings.API_ASSET_POST_MAX_SIZE


def get_s3_client() -> S3Client:
    """Return a new S3 client (not thread-safe).

    Boto should get credentials from ~/.aws/credentials or the environment.
    In particular, the following keys are required:

    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_DEFAULT_REGION
    - AWS_ENDPOINT_URL
    """
    return boto3.client("s3")


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
) -> dict:
    paginator = s3_client.get_paginator("list_objects_v2")
    files = {}
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
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
