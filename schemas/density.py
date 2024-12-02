
from pydantic import BaseModel
from typing import Optional
from schemas.base import (
    CreationMixin,
    LicensedReadMixin,
    LicensedCreateMixin,
    BrainLocationCreate,
    BrainRegionRead,
    SpeciesRead,
    StrainRead,
)

class ExperimentalDensityBase(BaseModel):
    name: str
    description: str
    brain_location: Optional[BrainLocationCreate]
    class Config:
        orm_mode = True
        from_attributes = True



class ExperimentalDensityCreate(ExperimentalDensityBase, LicensedCreateMixin):
    species_id: int
    strain_id: int
    brain_region_id: int
    legacy_id: Optional[str]



class ExperimentalDensityRead(
    ExperimentalDensityBase, CreationMixin, LicensedReadMixin
):
    species: SpeciesRead
    strain: Optional[StrainRead]
    brain_region: BrainRegionRead

class ExperimentalNeuronDensityCreate(ExperimentalDensityCreate):
    pass
class ExperimentalBoutonDensityCreate(ExperimentalDensityCreate):
    pass
class ExperimentalSynapsesPerConnectionCreate(ExperimentalDensityCreate):
    pass
class ExperimentalNeuronDensityRead(ExperimentalDensityRead):
    pass
class ExperimentalBoutonDensityRead(ExperimentalDensityRead):
    pass
class ExperimentalSynapsesPerConnectionRead(ExperimentalDensityRead):
    pass