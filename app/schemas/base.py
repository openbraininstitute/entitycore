import uuid
from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict

from app.db.types import EntityType


class EntityTypeMixin(BaseModel):
    type: EntityType | None = None


class AuthorizationMixin(BaseModel):
    authorized_project_id: UUID4
    authorized_public: bool = False


class AuthorizationOptionalPublicMixin(BaseModel):
    authorized_public: bool = False


class ProjectContext(BaseModel):
    virtual_lab_id: UUID4
    project_id: UUID4


class OptionalProjectContext(BaseModel):
    virtual_lab_id: UUID4 | None = None
    project_id: UUID4 | None = None


class IdentifiableMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class CreationMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    creation_date: datetime
    update_date: datetime

    def dict(self, **kwargs):
        result = super().model_dump(**kwargs)
        result["creation_date"] = (
            result["creation_date"].isoformat() if result["creation_date"] else None
        )
        result["update_date"] = result["update_date"].isoformat() if result["update_date"] else None
        return result


class LicenseCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    label: str


class LicenseRead(LicenseCreate, CreationMixin, IdentifiableMixin):
    pass


class BrainRegionRead(IdentifiableMixin, CreationMixin):
    model_config = ConfigDict(from_attributes=True)

    annotation_value: int
    name: str
    acronym: str
    color_hex_triplet: str
    parent_structure_id: uuid.UUID | None
    hierarchy_id: uuid.UUID


class BrainRegionCreateMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    brain_region_id: uuid.UUID


class BrainRegionReadMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    brain_region: BrainRegionRead


class StrainCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    taxonomy_id: str
    species_id: uuid.UUID


class StrainRead(StrainCreate, CreationMixin, IdentifiableMixin):
    pass


class LicensedCreateMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    license_id: uuid.UUID | None = None


class LicensedReadMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    license: LicenseRead | None


class BasicEntityRead(IdentifiableMixin, EntityTypeMixin):
    pass
