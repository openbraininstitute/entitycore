from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import CreationMixin, IdentifiableMixin


class SpeciesCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    taxonomy_id: str
    embedding: SkipJsonSchema[list[float] | None] = None


class SpeciesRead(SpeciesCreate, CreationMixin, CreatedByUpdatedByMixin, IdentifiableMixin):
    embedding: list[float] | None = Field(default=None, exclude=True)


class NestedSpeciesRead(SpeciesCreate, IdentifiableMixin):
    pass


class StrainCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    taxonomy_id: str
    species_id: UUID
    embedding: SkipJsonSchema[list[float] | None] = None


class StrainRead(StrainCreate, CreationMixin, CreatedByUpdatedByMixin, IdentifiableMixin):
    embedding: list[float] | None = Field(default=None, exclude=True)


class NestedStrainRead(StrainCreate, IdentifiableMixin):
    embedding: list[float] | None = Field(default=None, exclude=True)
