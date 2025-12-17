"""Asset repository module."""

import uuid

import sqlalchemy as sa

from app.db.model import Asset, Entity
from app.db.types import AssetStatus, EntityType
from app.repository.base import BaseRepository
from app.schemas.asset import AssetCreate


class AssetRepository(BaseRepository):
    """AssetRepository."""

    def get_entity_asset(
        self,
        entity_type: EntityType,
        entity_id: uuid.UUID,
        asset_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> Asset:
        """Return a single asset, or raise an error."""
        query = (
            sa.select(Asset)
            .join(Entity, Entity.id == Asset.entity_id)
            .where(
                Asset.entity_id == entity_id,
                Asset.id == asset_id,
                Entity.type == entity_type.name,
            )
        )
        # See: https://github.com/openbraininstitute/entitycore/issues/358
        if not include_deleted:
            query = query.where(Asset.status != AssetStatus.DELETED)

        return self.db.execute(query).scalar_one()

    def create_entity_asset(self, entity_id: uuid.UUID, asset: AssetCreate) -> Asset:
        """Create an asset associated with the given entity."""
        sha256_digest = bytes.fromhex(asset.sha256_digest) if asset.sha256_digest else None
        db_asset = Asset(
            status=AssetStatus.CREATED,
            entity_id=entity_id,
            path=asset.path,
            full_path=asset.full_path,
            is_directory=asset.is_directory,
            content_type=asset.content_type,
            size=asset.size,
            sha256_digest=sha256_digest,
            meta=asset.meta,
            label=asset.label,
            storage_type=asset.storage_type,
            created_by_id=asset.created_by_id,
            updated_by_id=asset.updated_by_id,
        )
        self.db.add(db_asset)
        self.db.flush()
        return db_asset

    def delete_entity_asset(
        self,
        entity_type: EntityType,
        entity_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> Asset:
        """Delete an entity asset."""
        query = sa.select(Asset).where(
            Asset.entity_id == entity_id,
            Asset.id == asset_id,
            Entity.type == entity_type.name,
            Entity.id == Asset.entity_id,
        )
        asset = self.db.execute(query).scalar_one()
        self.db.delete(asset)
        self.db.flush()
        return asset
