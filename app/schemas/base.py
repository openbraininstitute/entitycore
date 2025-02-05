from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreationMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    creation_date: datetime
    update_date: datetime

    def dict(self, **kwargs):
        result = super().dict(**kwargs)
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


class LicenseRead(LicenseCreate, CreationMixin):
    pass


class BrainLocationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    x: float
    y: float
    z: float


class BrainRegionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    acronym: str
    children: list[int]


class BrainRegionRead(BrainRegionCreate, CreationMixin):
    pass


class StrainCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    taxonomy_id: str
    species_id: int


class StrainRead(StrainCreate, CreationMixin):
    pass


class SpeciesCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    taxonomy_id: str


class SpeciesRead(SpeciesCreate, CreationMixin):
    pass


class LicensedCreateMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    license_id: int | None = None


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
