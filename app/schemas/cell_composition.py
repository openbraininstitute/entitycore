from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.brain_region import BrainRegionCreateMixin, BrainRegionReadMixin
from app.schemas.entity import EntityCreate, EntityRead
from app.schemas.species import SpeciesStrainCreateMixin, SpeciesStrainReadMixin
from app.schemas.utils import make_update_schema


class CellCompositionBaseMixin(NameDescriptionMixin):
    pass


class CellCompositionCreate(
    CellCompositionBaseMixin,
    BrainRegionCreateMixin,
    SpeciesStrainCreateMixin,
    EntityCreate,
):
    pass


CellCompositionUserUpdate = make_update_schema(CellCompositionCreate, "CellCompositionUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
CellCompositionAdminUpdate = make_update_schema(
    CellCompositionCreate,
    "CellCompositionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class CellCompositionRead(
    CellCompositionBaseMixin,
    BrainRegionReadMixin,
    SpeciesStrainReadMixin,
    EntityRead,
):
    pass
