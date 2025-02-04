"""Asset repository module."""

import uuid
from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa

from app.db.model import Asset
from app.db.types import AssetStatus, EntityType
from app.repository.base import BaseRepository
from app.schemas.asset import AssetCreate


class AssetRepository(BaseRepository):
    """AssetRepository."""

    def get_entity_assets(
        self,
        entity_type: EntityType,
        entity_id: int,
    ) -> Sequence[Asset]:
        """Return a sequence of assets, potentially empty."""
        query = sa.select(Asset).where(
            Asset.entity_type == entity_type,
            Asset.entity_id == entity_id,
        )
        return self.db.execute(query).scalars().all()

    def get_entity_asset(
        self,
        entity_type: EntityType,
        entity_id: int,
        asset_id: UUID,
    ) -> Asset:
        """Return a single asset, or raise an error."""
        query = sa.select(Asset).where(
            Asset.entity_type == entity_type,
            Asset.entity_id == entity_id,
            Asset.uuid == asset_id,
        )
        return self.db.execute(query).scalar_one()

    def create_entity_asset(
        self, entity_type: EntityType, entity_id: int, asset: AssetCreate
    ) -> Asset:
        """Create an asset associated with the given entity."""
        query = (
            sa.insert(Asset)
            .values(
                uuid=uuid.uuid4(),
                status=AssetStatus.CREATED,
                entity_id=entity_id,
                entity_type=entity_type,
                path=asset.path,
                fullpath=asset.fullpath,
                bucket_name=asset.bucket_name,
                is_directory=asset.is_directory,
                content_type=asset.content_type,
                size=asset.size,
                meta=asset.meta,
            )
            .returning(Asset)
        )
        return self.db.execute(query).scalar_one()

    def update_entity_asset_status(
        self,
        entity_type: EntityType,
        entity_id: int,
        asset_id: UUID,
        asset_status: AssetStatus,
    ) -> Asset:
        """Update the status of the given asset.

        Raise an error if any of the following is true:

        - the asset doesn't exist for the given entity
        - the status is already set with the same requested value
        """
        query = (
            sa.update(Asset)
            .values(status=asset_status)
            .where(
                Asset.entity_type == entity_type,
                Asset.entity_id == entity_id,
                Asset.uuid == asset_id,
                Asset.status != asset_status,
            )
            .returning(Asset)
        )
        return self.db.execute(query).scalar_one()
