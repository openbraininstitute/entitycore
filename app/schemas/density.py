from pydantic import BaseModel, ConfigDict

from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    LicensedCreateMixin,
    LicensedReadMixin,
    SpeciesRead,
    StrainRead,
)


class ExperimentalDensityBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str


class ExperimentalDensityCreate(
    ExperimentalDensityBase, LicensedCreateMixin, AuthorizationOptionalPublicMixin
):
    species_id: int
    strain_id: int
    brain_region_id: int
    legacy_id: str | None


class ExperimentalDensityRead(
    ExperimentalDensityBase, CreationMixin, LicensedReadMixin, AuthorizationMixin
):
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
