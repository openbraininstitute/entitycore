from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import CreationMixin, IdentifiableMixin
from app.schemas.utils import make_update_schema


class SpeciesCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    taxonomy_id: str


class SpeciesRead(SpeciesCreate, CreationMixin, CreatedByUpdatedByMixin, IdentifiableMixin):
    pass


SpeciesAdminUpdate = make_update_schema(
    SpeciesCreate,
    "SpeciesAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedSpeciesRead(SpeciesCreate, IdentifiableMixin):
    pass


class StrainCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    taxonomy_id: str
    species_id: UUID


class StrainRead(StrainCreate, CreationMixin, CreatedByUpdatedByMixin, IdentifiableMixin):
    pass


StrainAdminUpdate = make_update_schema(
    StrainCreate,
    "StrainAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedStrainRead(StrainCreate, IdentifiableMixin):
    pass
