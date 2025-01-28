from datetime import datetime
from typing import List, Optional, Field, Dict

from pydantic import BaseModel

from app.schemas.contribution import ContributionBase


class CreationMixin(BaseModel):
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

    class Config:
        from_attributes = True


class LicenseCreate(BaseModel):
    name: str
    description: str

    class Config:
        from_attributes = True


class LicenseRead(LicenseCreate, CreationMixin):
    pass


class BrainLocationCreate(BaseModel):
    x: float
    y: float
    z: float

    class Config:
        from_attributes = True


class BrainRegionCreate(BaseModel):
    ontology_id: str
    name: str
    acronym: Optional[str] = Field(
        None, description="should be allen notation acronym if it exists"
    )

    class Config:
        from_attributes = True


class BrainRegionRead(BrainRegionCreate, CreationMixin):
    pass


class StrainCreate(BaseModel):
    name: str
    taxonomy_id: str
    species_id: int

    class Config:
        from_attributes = True


class StrainRead(StrainCreate, CreationMixin):
    pass


class SpeciesCreate(BaseModel):
    name: str
    taxonomy_id: str

    class Config:
        from_attributes = True


class SpeciesRead(SpeciesCreate, CreationMixin):
    pass


class SubjectCreate(BaseModel):
    strain_id: int = Field(
        None,
        title="Strain ID",
        description="ID of the strain associated with the subject.",
    )
    age: Optional[int] = Field(
        None,
        title="Age",
        description="Age of the subject in days.",
    )
    sex: Optional[str] = Field(
        None,
        title="Sex",
        description="Sex of the subject (e.g., 'male', 'female').",
    )
    weight: Optional[float] = Field(
        None,
        title="Weight",
        description="Weight of the subject in grams.",
    )


class SubjectRead(BaseModel, CreationMixin):
    strain: StrainRead = Field(
        ..., title="Strain", description="Detailed information about the subject's strain."
    )
    age: Optional[int]
    sex: Optional[str]
    weight: Optional[float]


class LicensedCreateMixin(BaseModel):
    license_id: int | None = None

    class Config:
        from_attributes = True


class LicensedReadMixin(BaseModel):
    license: LicenseRead | None

    class Config:
        from_attributes = True


class MorphologyMeasurementSerieBase(BaseModel):
    name: str
    value: float

    class Config:
        from_attributes = True


class MeasurementCreate(BaseModel):
    measurement_of: str
    measurement_serie: list[MorphologyMeasurementSerieBase]

    class Config:
        from_attributes = True


class MeasurementRead(MeasurementCreate):
    id: int


class BaseDataModel(LicensedCreateMixin):
    """
    Base Data Model schema that will be inherited by all data schemas.
    """

    name: str
    description: str
    contributon: list[ContributionBase]


class SingleCellData(BaseModel):
    brain_region: BrainRegionCreate
    subject_id: int = Field(
        ...,
        title="Subject ID",
        description="ID of the subject",
    )


class File(BaseDataModel):
    path: str = Field(..., title="File Path", description="Path or URL to the file.")
    format: str = Field(..., title="File Format", description="Format of the file (e.g., nwb, h5).")
    size: Optional[int] = Field(None, title="File Size", description="Size of the file in bytes.")
