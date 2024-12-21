
from pydantic import BaseModel

from app.schemas.base import (
    BrainLocationCreate,
    BrainRegionRead,
    CreationMixin,
    LicensedCreateMixin,
    LicensedReadMixin,
    SpeciesRead,
    StrainRead,
)


class ExperimentalDensityBase(BaseModel):
    name: str
    description: str
    brain_location: BrainLocationCreate | None

    class Config:
        from_attributes = True


class ExperimentalDensityCreate(ExperimentalDensityBase, LicensedCreateMixin):
    species_id: int
    strain_id: int
    brain_region_id: int
    legacy_id: str | None


class ExperimentalDensityRead(ExperimentalDensityBase, CreationMixin, LicensedReadMixin):
    species: SpeciesRead
    strain: StrainRead | None
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
