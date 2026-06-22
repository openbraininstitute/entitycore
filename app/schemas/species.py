from uuid import UUID

from app.schemas.base import Schema
from app.schemas.identifiable import IdentifiableCreate, IdentifiableRead, NestedIdentifiableRead
from app.schemas.utils import make_update_schema


class SpeciesBase(Schema):
    name: str
    taxonomy_id: str


class SpeciesCreate(SpeciesBase, IdentifiableCreate):
    pass


class SpeciesRead(SpeciesBase, IdentifiableRead):
    pass


SpeciesAdminUpdate = make_update_schema(
    SpeciesCreate,
    "SpeciesAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedSpeciesRead(SpeciesBase, NestedIdentifiableRead):
    pass


class StrainBase(Schema):
    name: str
    taxonomy_id: str
    species_id: UUID


class StrainCreate(StrainBase, IdentifiableCreate):
    pass


class StrainRead(StrainBase, IdentifiableRead):
    pass


StrainAdminUpdate = make_update_schema(
    StrainCreate,
    "StrainAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedStrainRead(StrainBase, NestedIdentifiableRead):
    pass


class SpeciesStrainReadMixin(Schema):
    species: NestedSpeciesRead
    strain: NestedStrainRead | None = None


class SpeciesStrainCreateMixin(Schema):
    species_id: UUID
    strain_id: UUID | None = None
