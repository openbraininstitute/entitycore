import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.asset import AssetsMixin
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import CreationMixin, IdentifiableMixin
from app.schemas.species import NestedSpeciesRead


class BrainAtlasBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    hierarchy_id: uuid.UUID
    species: NestedSpeciesRead


class BrainAtlasRead(BrainAtlasBase, CreationMixin, CreatedByUpdatedByMixin, IdentifiableMixin, AssetsMixin):
    pass


class BrainAtlasRegionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    volume: float | None
    is_leaf_region: bool

    brain_atlas_id: uuid.UUID
    brain_region_id: uuid.UUID


class BrainAtlasRegionRead(BrainAtlasRegionBase, CreationMixin, IdentifiableMixin, AssetsMixin):
    pass
