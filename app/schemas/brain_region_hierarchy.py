
from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import CreationMixin, IdentifiableMixin
from app.schemas.species import SpeciesStrainCreateMixin, SpeciesStrainReadMixin
from app.schemas.utils import make_update_schema


class BrainRegionHierarchyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str


class BrainRegionHierarchyCreate(BrainRegionHierarchyBase, SpeciesStrainCreateMixin):
    pass


class BrainRegionHierarchyRead(
    BrainRegionHierarchyBase,
    CreationMixin,
    CreatedByUpdatedByMixin,
    IdentifiableMixin,
    SpeciesStrainReadMixin,
):
    pass


BrainRegionHierarchyAdminUpdate = make_update_schema(
    BrainRegionHierarchyCreate,
    "BrainRegionHierarchyAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
