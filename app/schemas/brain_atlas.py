import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.base import CreationMixin, IdentifiableMixin, SpeciesRead


class BrainAtlasBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    hierarchy_id: uuid.UUID
    species: SpeciesRead


class BrainAtlasRead(BrainAtlasBase, CreationMixin, IdentifiableMixin):
    pass


class BrainAtlasRegionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    volume: float
    leaf_region: bool

    brain_atlas_id: uuid.UUID
    brain_region_id: uuid.UUID


class BrainAtlasRegionRead(BrainAtlasRegionBase, CreationMixin, IdentifiableMixin):
    pass
