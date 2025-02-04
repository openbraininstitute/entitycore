"""Asset repository module."""

import uuid
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Sequence

from app.db.model import Asset, AssetEntity
from app.db.types import AssetStatus, EntityType
from app.repository.base import BaseRepository


class AssetRepository(BaseRepository):
    """AssetRepository."""

    def get_entity_assets(
        self,
        entity_type: EntityType,
        entity_id: int,
    ) -> Sequence[Asset]:
        """."""
        query = (
            sa.select(Asset)
            .join(AssetEntity)
            .where(
                AssetEntity.entity_type == entity_type,
                AssetEntity.entity_id == entity_id,
            )
        )
        return self.db.execute(query).scalars().all()

    def get_entity_asset(
        self,
        entity_type: EntityType,
        entity_id: int,
        asset_id: UUID,
    ) -> Asset:
        query = (
            sa.select(Asset)
            .join(AssetEntity)
            .where(
                AssetEntity.entity_type == entity_type,
                AssetEntity.entity_id == entity_id,
                Asset.uuid == asset_id,
            )
        )
        return self.db.execute(query).scalar_one()

    def create_entity_asset(self, entity_type: EntityType, entity_id: int, **kwargs) -> Asset:
        query = (
            sa.insert(Asset)
            .values(uuid=uuid.uuid4(), status=AssetStatus.CREATED, **kwargs)
            .returning(Asset)
        )
        asset = self.db.execute(query).scalar_one()
        query = sa.insert(AssetEntity).values(
            asset_id=asset.id,
            entity_id=entity_id,
            entity_type=entity_type,
        )
        self.db.execute(query)
        return asset

    def update_entity_asset_status(
        self,
        entity_type: EntityType,
        entity_id: int,
        asset_id: UUID,
        asset_status: AssetStatus,
    ) -> Asset:
        query = (
            sa.update(Asset)
            .values(status=asset_status)
            .where(
                AssetEntity.asset_id == Asset.id,
                AssetEntity.entity_type == entity_type,
                AssetEntity.entity_id == entity_id,
                Asset.uuid == asset_id,
                Asset.status != asset_status,
            )
            .returning(Asset)
        )
        return self.db.execute(query).scalar_one()
