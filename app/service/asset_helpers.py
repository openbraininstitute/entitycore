from http import HTTPStatus

from types_boto3_s3 import S3Client

from app.config import StorageUnion, storages
from app.db.model import Asset
from app.db.types import AssetStatus, ContentType
from app.errors import ApiError, ApiErrorCode
from app.schemas.asset import (
    AssetRead,
    AssetReadWithUploadMeta,
    ToUploadPart,
    UploadMeta,
    UploadMetaRead,
)
from app.utils.s3 import (
    check_object,
    generate_presigned_url,
    multipart_compute_upload_plan,
    multipart_upload_complete,
    multipart_upload_create_part_presigned_url,
    multipart_upload_initiate,
    multipart_upload_list_parts,
)


def build_asset_read_with_upload_meta(
    asset: Asset, parts: list[ToUploadPart]
) -> AssetReadWithUploadMeta:
    """Build AssetReadWithUploadMeta from an asset and its presigned URL parts."""
    # The presigned urls are not stored in the db because not needed and potentially too numerous.
    # The upload_id is not provided in the response because it is not needed by the client.
    base = AssetRead.model_validate(asset)
    upload_meta = UploadMeta.model_validate(asset.upload_meta)
    upload_meta_read = UploadMetaRead(part_size=upload_meta.part_size, parts=parts)
    return AssetReadWithUploadMeta.model_validate(
        {**base.model_dump(), "upload_meta": upload_meta_read.model_dump()}
    )


def generate_upload_presigned_urls(
    *,
    s3_client: S3Client,
    asset: Asset,
) -> list[ToUploadPart]:
    """Generate presigned URLs for uploading an asset. Thread-safe, no DB access.

    For empty files, multipart upload is not possible. In that case a single presigned
    ``put_object`` URL is returned as ``[ToUploadPart(part_number=0, url=...)]``
    so the client can process it the same way as multipart parts.
    """
    asset_storage = storages[asset.storage_type]
    upload_meta = UploadMeta.model_validate(asset.upload_meta)
    if asset.size > 0:
        return [
            ToUploadPart(
                part_number=pn,
                url=multipart_upload_create_part_presigned_url(
                    s3_client=s3_client,
                    bucket=asset_storage.bucket,
                    s3_key=asset.full_path,
                    upload_id=upload_meta.upload_id,
                    part_number=pn,
                ),
            )
            for pn in range(1, upload_meta.part_count + 1)
        ]
    url = generate_presigned_url(
        s3_client=s3_client,
        operation="put_object",
        bucket_name=asset_storage.bucket,
        s3_key=asset.full_path,
    )
    if url is None:
        raise ApiError(
            message=f"Could not create presigned url for {asset.full_path}",
            error_code=ApiErrorCode.S3_CANNOT_CREATE_PRESIGNED_URL,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    return [ToUploadPart(part_number=0, url=url)]


def initiate_multipart_upload(
    *,
    s3_client: S3Client,
    s3_key: str,
    bucket: str,
    content_type: ContentType,
    filesize: int,
    preferred_part_count: int,
) -> UploadMeta:
    """Initiate a single multipart upload and return the UploadMeta. Thread-safe, no DB access."""
    if filesize > 0:
        part_size, part_count = multipart_compute_upload_plan(
            filesize=filesize,
            preferred_part_count=preferred_part_count,
        )
        upload_id = multipart_upload_initiate(
            s3_client=s3_client,
            s3_key=s3_key,
            bucket=bucket,
            content_type=content_type,
        )
        return UploadMeta(upload_id=upload_id, part_size=part_size, part_count=part_count)
    return UploadMeta(upload_id="", part_size=0, part_count=0)


def complete_asset_s3(
    *,
    asset: Asset,
    storage: StorageUnion,
    s3_client: S3Client,
) -> None:
    """Verify and complete the S3 multipart upload for a single asset.

    This is the pure I/O layer: no DB writes, thread-safe.
    Raises ApiError if validation fails.
    """
    upload_meta = UploadMeta.model_validate(asset.upload_meta) if asset.upload_meta else None
    if asset.status != AssetStatus.UPLOADING or upload_meta is None:
        raise ApiError(
            message="Asset is not uploading. Operation cannot be performed.",
            error_code=ApiErrorCode.ASSET_NOT_UPLOADING,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    # parts that have been already uploaded to s3
    uploaded_parts = multipart_upload_list_parts(
        s3_client=s3_client,
        bucket=storage.bucket,
        s3_key=asset.full_path,
        upload_id=upload_meta.upload_id,
    )
    # verify that expected and uploaded agree
    uploaded_part_numbers = {p["PartNumber"] for p in uploaded_parts}
    expected_part_numbers = set(range(1, upload_meta.part_count + 1))
    if uploaded_part_numbers != expected_part_numbers:
        raise ApiError(
            message=(
                "Expected parts are not uploaded. "
                f"Expected: {len(expected_part_numbers)}, Actual: {len(uploaded_part_numbers)}"
            ),
            error_code=ApiErrorCode.ASSET_UPLOAD_INCOMPLETE,
            http_status_code=HTTPStatus.CONFLICT,
        )
    upload_size = sum(p["Size"] for p in uploaded_parts)
    if upload_size != asset.size:
        raise ApiError(
            message=(
                "Total from multipart upload parts sizes does not match expected size. "
                f"Expected: {asset.size}, Actual: {upload_size}"
            ),
            error_code=ApiErrorCode.ASSET_UPLOAD_INCONSISTENT_SIZE,
            http_status_code=HTTPStatus.CONFLICT,
        )
    multipart_upload_complete(
        s3_client=s3_client,
        s3_key=asset.full_path,
        upload_id=upload_meta.upload_id,
        bucket=storage.bucket,
        parts=uploaded_parts,
    )


def complete_empty_asset_s3(
    *,
    asset: Asset,
    storage: StorageUnion,
    s3_client: S3Client,
) -> None:
    """Verify that an empty file was uploaded to S3.

    This is the pure I/O layer: no DB writes, thread-safe.
    Raises ApiError if validation fails.
    """
    upload_meta = UploadMeta.model_validate(asset.upload_meta) if asset.upload_meta else None
    if asset.status != AssetStatus.UPLOADING or upload_meta is None:
        raise ApiError(
            message="Asset is not uploading. Operation cannot be performed.",
            error_code=ApiErrorCode.ASSET_NOT_UPLOADING,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )
    try:
        check_result = check_object(
            s3_client,
            bucket_name=storage.bucket,
            s3_key=asset.full_path,
            is_directory=False,
        )
    except Exception as e:
        raise ApiError(
            message="Failed to check object.",
            error_code=ApiErrorCode.GENERIC_ERROR,
            http_status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        ) from e
    if not check_result["exists"]:
        raise ApiError(
            message="Uploaded empty file not found.",
            error_code=ApiErrorCode.ASSET_UPLOAD_INCOMPLETE,
            http_status_code=HTTPStatus.CONFLICT,
        )
    if check_result["size"] != 0:
        raise ApiError(
            message=(
                "Uploaded empty file does not match expected size. "
                f"Expected: 0, Actual: {check_result['size']}"
            ),
            error_code=ApiErrorCode.ASSET_UPLOAD_INCONSISTENT_SIZE,
            http_status_code=HTTPStatus.CONFLICT,
        )
