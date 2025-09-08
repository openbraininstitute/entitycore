import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict

from app.db.model import ValidationStatus
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.annotation import ETypeClassRead, MTypeClassRead
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    BrainRegionRead,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.emodel import EModelRead
from app.schemas.memodel_calibration_result import MEModelCalibrationResultRead
from app.schemas.morphology import ReconstructionMorphologyRead
from app.schemas.species import NestedSpeciesRead, NestedStrainRead
from app.schemas.utils import make_update_schema


class MEModelBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    validation_status: ValidationStatus = ValidationStatus.created


# To be used by entities who reference MEModel
class NestedMEModel(MEModelBase, CreationMixin, IdentifiableMixin):
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None


class MEModelCreate(MEModelBase, AuthorizationOptionalPublicMixin):
    brain_region_id: uuid.UUID
    morphology_id: uuid.UUID
    emodel_id: uuid.UUID
    species_id: uuid.UUID
    strain_id: uuid.UUID | None = None


MEModelUpdate = Annotated[BaseModel, make_update_schema(MEModelCreate, "MEModelUpdate")]


class MEModelRead(
    MEModelBase,
    CreationMixin,
    AuthorizationMixin,
    EntityTypeMixin,
    CreatedByUpdatedByMixin,
    ContributionReadWithoutEntityMixin,
):
    id: uuid.UUID
    species: NestedSpeciesRead
    strain: NestedStrainRead | None
    brain_region: BrainRegionRead
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None
    morphology: ReconstructionMorphologyRead
    emodel: EModelRead
    calibration_result: MEModelCalibrationResultRead | None
