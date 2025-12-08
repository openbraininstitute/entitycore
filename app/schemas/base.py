import uuid
from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict

from app.db.types import ActivityType, EntityType
from app.schemas.utils import make_update_schema


class ActivityTypeMixin:
    type: ActivityType | None = None


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


class NameDescriptionMixin:
    name: str
    description: str


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


class LicenseCreate(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)
    label: str


class LicenseRead(LicenseCreate, CreationMixin, IdentifiableMixin):
    pass


LicenseAdminUpdate = make_update_schema(
    LicenseCreate,
    "LicenseAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class LicenseReadMixin:
    license: LicenseRead | None = None


class LicenseCreateMixin:
    license_id: uuid.UUID | None = None


class BrainRegionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    annotation_value: int
    name: str
    acronym: str
    color_hex_triplet: str
    parent_structure_id: uuid.UUID | None = None
    hierarchy_id: uuid.UUID


class BrainRegionRead(BrainRegionBase, IdentifiableMixin, CreationMixin):
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None


class BrainRegionCreate(BrainRegionBase):
    pass


BrainRegionAdminUpdate = make_update_schema(
    BrainRegionCreate,
    "BrainRegionAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class BrainRegionCreateMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    brain_region_id: uuid.UUID


class BrainRegionReadMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    brain_region: BrainRegionRead


class LicensedCreateMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    license_id: uuid.UUID | None = None


class LicensedReadMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    license: LicenseRead | None


class BasicEntityRead(IdentifiableMixin, EntityTypeMixin):
    pass
