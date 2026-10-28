import uuid

from app.schemas.base import Schema
from app.schemas.identifiable import IdentifiableCreate, NestedIdentifiableRead
from app.schemas.species import SpeciesStrainReadMixin
from app.schemas.utils import make_update_schema


class BrainRegionBase(Schema):
    annotation_value: int
    name: str
    acronym: str
    color_hex_triplet: str
    parent_structure_id: uuid.UUID | None = None
    hierarchy_id: uuid.UUID


class NestedBrainRegionRead(BrainRegionBase, NestedIdentifiableRead):
    pass


class BrainRegionRead(BrainRegionBase, SpeciesStrainReadMixin, NestedIdentifiableRead):
    pass


class BrainRegionCreate(BrainRegionBase, IdentifiableCreate):
    pass


BrainRegionAdminUpdate = make_update_schema(
    BrainRegionCreate,
    "BrainRegionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class BrainRegionCreateMixin(Schema):
    brain_region_id: uuid.UUID


class BrainRegionReadMixin(Schema):
    brain_region: NestedBrainRegionRead
