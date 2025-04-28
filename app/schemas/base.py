import uuid
from datetime import datetime, timedelta
from typing import Annotated, TYPE_CHECKING

from pydantic import UUID4, BaseModel, ConfigDict, Field, model_validator

from app.db.types import AgePeriod, Sex

from datetime import date


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


class BrainRegionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    acronym: str
    children: list[int]


class BrainRegionRead(BrainRegionCreate, CreationMixin):
    pass


class BrainRegionCreateMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    brain_region_id: int


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


class SpeciesCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    taxonomy_id: str


class SpeciesRead(SpeciesCreate, CreationMixin, IdentifiableMixin):
    pass


class LicensedCreateMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    license_id: uuid.UUID | None = None


class LicensedReadMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    license: LicenseRead | None

class MorphologyMeasurementSerieBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    value: float
    
class MeasurementCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    measurement_of: str
    measurement_serie: list[MorphologyMeasurementSerieBase]


class MeasurementRead(MeasurementCreate):
    id: int


class SubjectBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, ser_json_timedelta="float")
    name: str
    description: str
    sex: Annotated[
        Sex,
        Field(title="Sex", description="Sex of the subject"),
    ]
    weight: Annotated[
        float | None,
        Field(title="Weight", description="Weight (in grams unless units given)", gt=0.0),
    ] = None
    weight_unit: str = 'grams'
    age_value: Annotated[
        timedelta | None,
        Field(title="Age value", description="Age value interval.", gt=timedelta(0)),
    ] = None
    age_unit : str= 'days'
    age_min: Annotated[
        timedelta | None,
        Field(title="Minimum age range", description="Minimum age range", gt=timedelta(0)),
    ] = None
    age_max: Annotated[
        timedelta | None,
        Field(title="Maximum age range", description="Maximum age range", gt=timedelta(0)),
    ] = None
    age_period: AgePeriod | None = None

    @model_validator(mode="after")
    def age_period_mandatory_with_age_fields(self):
        """Age period must be provided when age fields are provided."""
        if any([self.age_value, self.age_min, self.age_max]) and not self.age_period:
            msg = "age_period must be provided when age fields are provided"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def either_age_value_or_age_range(self):
        """Either age_value or age_min and age_max must be provided."""
        if self.age_value and any([self.age_min, self.age_max]):
            msg = "age_value and age_min/age_max cannot both be provided"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def min_max_age_range_consistency(self):
        """Age min and max must be provided together or not at all."""
        if self.age_min and self.age_max:
            if self.age_min >= self.age_max:
                msg = "age_max must be greater than age_min"
                raise ValueError(msg)
            return self

        if self.age_min or self.age_max:
            msg = "age_min and age_max must be provided together"
            raise ValueError(msg)

        return self


class SubjectCreate(AuthorizationOptionalPublicMixin, SubjectBase):
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None

class SubjectRead(SubjectBase, CreationMixin, AuthorizationMixin, IdentifiableMixin):
    species: SpeciesRead
    strain: StrainRead
    name: str
    description: str
