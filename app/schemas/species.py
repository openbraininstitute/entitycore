from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import CreationMixin, IdentifiableMixin


class SpeciesCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    taxonomy_id: str


class SpeciesRead(SpeciesCreate, CreationMixin, CreatedByUpdatedByMixin, IdentifiableMixin):
    pass


class NestedSpeciesRead(SpeciesCreate, IdentifiableMixin):
    pass


class StrainCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    taxonomy_id: str
    species_id: UUID


class StrainRead(StrainCreate, CreationMixin, CreatedByUpdatedByMixin, IdentifiableMixin):
    pass


class NestedStrainRead(StrainCreate, IdentifiableMixin):
    pass
