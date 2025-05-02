import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.db.types import EntityType, MeasurementUnit
from app.schemas.annotation import ETypeClassRead, MTypeClassRead
from app.schemas.asset import AssetRead
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    LicensedCreateMixin,
    LicensedReadMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntity
from app.schemas.subject import SubjectRead


class MeasurementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    unit: MeasurementUnit
    value: float


class ExperimentalDensityBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str


class ExperimentalDensityCreate(
    ExperimentalDensityBase, LicensedCreateMixin, AuthorizationOptionalPublicMixin
):
    subject_id: uuid.UUID
    brain_region_id: int
    legacy_id: str | None


class ExperimentalDensityRead(
    ExperimentalDensityBase,
    CreationMixin,
    IdentifiableMixin,
    LicensedReadMixin,
    AuthorizationMixin,
    EntityTypeMixin,
):
    subject: SubjectRead
    brain_region: BrainRegionRead
    measurements: list[MeasurementRead] | None
    assets: list[AssetRead] | None
    contributions: list[ContributionReadWithoutEntity] | None


class ExperimentalNeuronDensityCreate(ExperimentalDensityCreate):
    pass


class ExperimentalBoutonDensityCreate(ExperimentalDensityCreate):
    pass


class ExperimentalSynapsesPerConnectionCreate(ExperimentalDensityCreate):
    synaptic_pathway_id: uuid.UUID


class ExperimentalNeuronDensityRead(ExperimentalDensityRead):
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None
    type: Literal[EntityType.experimental_neuron_density] = EntityType.experimental_neuron_density


class ExperimentalBoutonDensityRead(ExperimentalDensityRead):
    mtypes: list[MTypeClassRead] | None
    type: Literal[EntityType.experimental_bouton_density] = EntityType.experimental_bouton_density


class SynapticPathwayRead(CreationMixin, IdentifiableMixin):
    pre_mtype: MTypeClassRead
    post_mtype: MTypeClassRead
    pre_region: BrainRegionRead
    post_region: BrainRegionRead


class ExperimentalSynapsesPerConnectionRead(ExperimentalDensityRead):
    synaptic_pathway: SynapticPathwayRead
    type: Literal[EntityType.experimental_synapses_per_connection] = (
        EntityType.experimental_synapses_per_connection
    )
