import uuid

from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.entity import EntityCreate, EntityRead
from app.schemas.species import SpeciesStrainCreateMixin, SpeciesStrainReadMixin
from app.schemas.utils import make_update_schema


class BrainAtlasCreate(
    EntityCreate,
    NameDescriptionMixin,
    SpeciesStrainCreateMixin,
):
    hierarchy_id: uuid.UUID


class BrainAtlasRead(
    EntityRead,
    NameDescriptionMixin,
    SpeciesStrainReadMixin,
):
    hierarchy_id: uuid.UUID


BrainAtlasUpdate = make_update_schema(BrainAtlasCreate, "BrainAtlasUpdate")  # pyright: ignore [reportInvalidTypeForm]
BrainAtlasAdminUpdate = make_update_schema(
    BrainAtlasCreate,
    "BrainAtlasAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
