"""Asset repository module."""

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Row, Sequence

from app.db.model import Asset, AssetEntity
from app.db.types import AssetStatus, EntityType
from app.repository.base import BaseRepository


class AssetRepository(BaseRepository):
    """AssetRepository."""

    def get_entity_assets(
        self,
        entity_type: EntityType,
        entity_id: int,
    ) -> Sequence[Row]:
        """."""
        query = (
            sa.select(
                Asset.uuid,
                Asset.path,
                Asset.status,
            )
            .select_from(Asset)
            .join(AssetEntity)
            .where(
                AssetEntity.entity_type == entity_type,
                AssetEntity.entity_id == entity_id,
            )
        )
        return self.db.execute(query).all()

    def get_entity_asset(
        self,
        entity_type: EntityType,
        entity_id: int,
        asset_id: UUID,
    ) -> Row | None:
        query = (
            sa.select(
                Asset.uuid,
                Asset.path,
                Asset.status,
            )
            .select_from(Asset)
            .join(AssetEntity)
            .where(
                AssetEntity.entity_type == entity_type,
                AssetEntity.entity_id == entity_id,
                Asset.uuid == asset_id,
            )
        )
        return self.db.execute(query).one_or_none()

    def update_entity_asset_status(
        self,
        entity_type: EntityType,
        entity_id: int,
        asset_id: UUID,
        asset_status: AssetStatus,
    ) -> Asset | None:
        query = (
            sa.update(Asset)
            .values(status=asset_status)
            .where(
                AssetEntity.asset_id == Asset.id,
                AssetEntity.entity_type == entity_type,
                AssetEntity.entity_id == entity_id,
                Asset.uuid == asset_id,
            )
            .returning(Asset)
        )
        return self.db.execute(query).scalar_one_or_none()
