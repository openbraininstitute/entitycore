import uuid

from pydantic import BaseModel, ConfigDict

from app.db.model import ActivityStatus
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.annotation import ETypeClassRead, MTypeClassRead
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    NameDescriptionMixin,
)
from app.schemas.brain_region import BrainRegionReadMixin
from app.schemas.cell_morphology import CellMorphologyRead
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.emodel import EModelRead
from app.schemas.memodel_calibration_result import MEModelCalibrationResultRead
from app.schemas.species import NestedSpeciesRead, NestedStrainRead
from app.schemas.utils import make_update_schema


class MEModelBase(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)
    validation_status: ActivityStatus = ActivityStatus.created


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


MEModelUserUpdate = make_update_schema(MEModelCreate, "MEModelUserUpdate")  # pyright: ignore [reportInvalidTypeForm]

MEModelAdminUpdate = make_update_schema(
    MEModelCreate,
    "MEModelAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class MEModelRead(
    MEModelBase,
    CreationMixin,
    AuthorizationMixin,
    EntityTypeMixin,
    CreatedByUpdatedByMixin,
    ContributionReadWithoutEntityMixin,
    BrainRegionReadMixin,
):
    id: uuid.UUID
    species: NestedSpeciesRead
    strain: NestedStrainRead | None
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None
    morphology: CellMorphologyRead
    emodel: EModelRead
    calibration_result: MEModelCalibrationResultRead | None
