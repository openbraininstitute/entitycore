"""Asset repository module."""

from collections.abc import Sequence

import sqlalchemy as sa

from app.db.model import Asset, Root
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
        query = (
            sa.select(Asset)
            .join(Root, Root.id == Asset.entity_id)
            .where(
                Asset.entity_id == entity_id,
                Root.type == entity_type.name,
            )
        )
        return self.db.execute(query).scalars().all()

    def get_entity_asset(
        self,
        entity_type: EntityType,
        entity_id: int,
        asset_id: int,
    ) -> Asset:
        """Return a single asset, or raise an error."""
        query = (
            sa.select(Asset)
            .join(Root, Root.id == Asset.entity_id)
            .where(
                Asset.entity_id == entity_id,
                Asset.id == asset_id,
                Asset.status != AssetStatus.DELETED,
                Root.type == entity_type.name,
            )
        )
        return self.db.execute(query).scalar_one()

    def create_entity_asset(self, entity_id: int, asset: AssetCreate) -> Asset:
        """Create an asset associated with the given entity."""
        sha256_digest = bytes.fromhex(asset.sha256_digest) if asset.sha256_digest else None
        query = (
            sa.insert(Asset)
            .values(
                status=AssetStatus.CREATED,
                entity_id=entity_id,
                path=asset.path,
                full_path=asset.full_path,
                bucket_name=asset.bucket_name,
                is_directory=asset.is_directory,
                content_type=asset.content_type,
                size=asset.size,
                sha256_digest=sha256_digest,
                meta=asset.meta,
            )
            .returning(Asset)
        )
        return self.db.execute(query).scalar_one()

    def update_entity_asset_status(
        self,
        entity_type: EntityType,
        entity_id: int,
        asset_id: int,
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
                Asset.entity_id == entity_id,
                Asset.id == asset_id,
                Asset.status != asset_status,
                Root.type == entity_type.name,
                Root.id == Asset.entity_id,
            )
            .returning(Asset)
        )
        return self.db.execute(query).scalar_one()
