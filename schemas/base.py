
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CreationMixin(BaseModel):
    id: int
    creation_date: datetime
    update_date: datetime

    def dict(self, **kwargs):
        result = super().dict(**kwargs)
        result["creation_date"] = (
            result["creation_date"].isoformat() if result["creation_date"] else None
        )
        result["update_date"] = (
            result["update_date"].isoformat() if result["update_date"] else None
        )
        return result
    class Config:
        orm_mode = True
        from_attributes = True

class LicenseCreate(BaseModel):
    name: str
    description: str
    class Config:
        orm_mode = True
        from_attributes = True

class LicenseRead(LicenseCreate, CreationMixin):
    pass

class BrainLocationCreate(BaseModel):
    x: float
    y: float
    z: float

    class Config:
        orm_mode = True
        from_attributes = True


class BrainRegionCreate(BaseModel):
    ontology_id: str
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class BrainRegionRead(BrainRegionCreate, CreationMixin):
    pass

class StrainCreate(BaseModel):
    name: str
    taxonomy_id: str
    species_id: int

    class Config:
        orm_mode = True


class StrainRead(StrainCreate, CreationMixin):
    pass

class SpeciesCreate(BaseModel):
    name: str
    taxonomy_id: str

    class Config:
        orm_mode = True
        from_attributes = True


class SpeciesRead(SpeciesCreate, CreationMixin):
    pass

class LicensedCreateMixin(BaseModel):
    license_id: Optional[int] = None
    class Config:
        orm_mode = True
        from_attributes = True

class LicensedReadMixin(BaseModel):
    license: Optional[LicenseRead]
    class Config:
        orm_mode = True
        from_attributes = True



class MorphologyMeasurementSerieBase(BaseModel):
    name: str
    value: float

    class Config:
        orm_mode = True
        from_attributes = True


class MeasurementCreate(BaseModel):
    measurement_of: str
    measurement_serie: List[MorphologyMeasurementSerieBase]

    class Config:
        orm_mode = True
        from_attributes = True


class MeasurementRead(MeasurementCreate):
    id: int


