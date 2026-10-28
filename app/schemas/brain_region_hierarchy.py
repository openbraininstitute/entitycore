from app.schemas.base import Schema
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead
from app.schemas.species import SpeciesStrainCreateMixin, SpeciesStrainReadMixin
from app.schemas.utils import make_update_schema


class BrainRegionHierarchyBase(Schema):
    name: str


class BrainRegionHierarchyCreate(
    BrainRegionHierarchyBase, SpeciesStrainCreateMixin, IdentifiableCreate
):
    pass


class BrainRegionHierarchyRead(
    BrainRegionHierarchyBase,
    SpeciesStrainReadMixin,
    IdentifiableRead,
):
    pass


BrainRegionHierarchyAdminUpdate = make_update_schema(
    BrainRegionHierarchyCreate,
    "BrainRegionHierarchyAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
