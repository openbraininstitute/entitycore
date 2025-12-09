import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.base import CreationMixin, IdentifiableMixin, make_update_schema
from app.schemas.species import NestedSpeciesRead, NestedStrainRead


class BrainRegionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    annotation_value: int
    name: str
    acronym: str
    color_hex_triplet: str
    parent_structure_id: uuid.UUID | None = None
    hierarchy_id: uuid.UUID


class BrainRegionReadNested(BrainRegionBase, IdentifiableMixin, CreationMixin):
    pass


class BrainRegionRead(BrainRegionReadNested):
    species: NestedSpeciesRead
    strain: NestedStrainRead | None = None


class BrainRegionCreate(BrainRegionBase):
    pass


BrainRegionAdminUpdate = make_update_schema(
    BrainRegionCreate,
    "BrainRegionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class BrainRegionCreateMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    brain_region_id: uuid.UUID


class BrainRegionReadMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    brain_region: BrainRegionReadNested
