import uuid
from itertools import batched

import sqlalchemy as sa
from sqlalchemy.orm import Session
from types_boto3_s3 import S3Client

from app.config import StorageUnion
from app.db.model import Asset, Entity
from app.db.types import AssetStatus, StorageType
from app.db.utils import PUBLISHABLE_BASE_CLASSES, PublishableBaseModel
from app.logger import L
from app.schemas.publish import ChangeProjectVisibilityResponse, MoveAssetsResult
from app.utils.s3 import (
    convert_s3_path_visibility,
    get_s3_path_prefix,
    move_directory,
    move_file,
)

BATCH_SIZE = 500


def _set_base_class_visibility(
    db: Session,
    project_id: uuid.UUID,
    db_model_class: type[PublishableBaseModel],
    *,
    public: bool,
) -> int:
    """Update authorized_public in all the resources of a single base class.

    Rows are updated directly without loading the ORM models, so it's not possible to fire any
    SQLAlchemy event, but it is more efficient as it avoids loading all the resources in memory.

    Returns the number of updated resources.
    """
    result = db.execute(
        sa.update(db_model_class)
        .where(
            db_model_class.authorized_project_id == project_id,
            db_model_class.authorized_public.is_(not public),
        )
        .values(
            authorized_public=public,
            update_date=db_model_class.update_date,  # preserve update_date
        )
    )
    return result.rowcount  # type: ignore[attr-defined]


def _set_assets_visibility(
    db: Session,
    *,
    s3_client: S3Client,
    project_id: uuid.UUID,
    bucket_name: str,
    storage_type: StorageType,
    max_assets: int | None,
    dry_run: bool,
    public: bool,
) -> MoveAssetsResult:
    """Move assets from private to public in S3 or vice versa, and update their path in the db.

    Rows are updated in batches directly after loading the ORM models for better efficiency.

    This function must be called after the entities have been converted to public (private).
    It ignores any private (public) entity added concurrently, because the query applies
    a filter on `Entity.authorized_public`.

    Returns the total number of assets and files moved, and their total size.
    """
    old_prefix = get_s3_path_prefix(public=not public)
    private_assets = db.execute(
        sa.select(Asset)
        .join(Entity, Entity.id == Asset.entity_id)
        .where(
            Entity.authorized_project_id == project_id,
            Entity.authorized_public.is_(public),
            Asset.storage_type == storage_type,
            Asset.status == AssetStatus.CREATED,
            Asset.full_path.like(f"{old_prefix}%"),
        )
        .with_for_update(of=Asset)
        .limit(max_assets)
    ).scalars()
    move_result = MoveAssetsResult()
    for batch in batched(private_assets, BATCH_SIZE):
        path_mapping: dict[uuid.UUID, str] = {}
        L.info("Processing batch of {} assets [dry_run={}]", len(batch), dry_run)
        for asset in batch:
            src_key = asset.full_path
            dst_key = convert_s3_path_visibility(asset.full_path, public=public)
            if asset.is_directory:
                move_result.update_from_directory_result(
                    move_directory(
                        s3_client,
                        src_bucket_name=bucket_name,
                        dst_bucket_name=bucket_name,
                        src_key=src_key,
                        dst_key=dst_key,
                        dry_run=dry_run,
                    )
                )
            else:
                move_result.update_from_file_result(
                    move_file(
                        s3_client,
                        src_bucket_name=bucket_name,
                        dst_bucket_name=bucket_name,
                        src_key=src_key,
                        dst_key=dst_key,
                        size=asset.size,
                        dry_run=dry_run,
                    )
                )
            path_mapping[asset.id] = dst_key
            db.expunge(asset)  # free memory from session's identity map
        db.execute(
            sa.update(Asset)
            .where(Asset.id.in_(path_mapping))
            .values(
                full_path=sa.case(path_mapping, value=Asset.id),
                update_date=Asset.update_date,  # preserve update_date
            )
        )
    return move_result


def set_project_visibility(
    db: Session,
    *,
    s3_client: S3Client,
    project_id: uuid.UUID,
    storage: StorageUnion,
    max_assets: int | None,
    dry_run: bool,
    public: bool = True,
) -> ChangeProjectVisibilityResponse:
    """Change the visibility of entities, activities, classifications, and assets in a project.

    If public is True, all the resources are made public.
    If public is False, all the resources are made private if possible, or it should fail
    if any resource has been used in other projects.

    The function can be called multiple times sequentially, to update max_assets per request.
    """
    savepoint = db.begin_nested()
    description = "public" if public else "private"
    resource_count = 0
    for db_model_class in PUBLISHABLE_BASE_CLASSES:
        L.info(
            "Updating table {} to {} for project {} [dry_run={}]",
            db_model_class.__tablename__,
            description,
            project_id,
            dry_run,
        )
        resource_count += _set_base_class_visibility(
            db=db,
            project_id=project_id,
            db_model_class=db_model_class,
            public=public,
        )
    L.info("Updating assets to {} for project {} [dry_run={}]", description, project_id, dry_run)
    move_result = _set_assets_visibility(
        db=db,
        s3_client=s3_client,
        project_id=project_id,
        bucket_name=storage.bucket,
        storage_type=storage.type,
        max_assets=max_assets,
        dry_run=dry_run,
        public=public,
    )
    if dry_run:
        savepoint.rollback()
        db.expire_all()
    completed = max_assets is None or move_result.asset_count < max_assets
    return ChangeProjectVisibilityResponse(
        message=f"Project resources successfully made {description}",
        project_id=project_id,
        resource_count=resource_count,
        move_assets_result=move_result,
        dry_run=dry_run,
        public=public,
        completed=completed,
    )
