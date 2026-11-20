import uuid

from app.db.types import ValidationStatus
from app.schemas.annotation import ETypeClassRead, MTypeClassRead
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.brain_region import BrainRegionReadMixin
from app.schemas.cell_morphology import CellMorphologyRead
from app.schemas.classification import ETypeClassIdsCreateMixin, MTypeClassIdsCreateMixin
from app.schemas.emodel import EModelRead
from app.schemas.entity import EntityCreate, EntityReadWoutAssets, NestedEntityRead
from app.schemas.memodel_calibration_result import NestedMEModelCalibrationResultRead
from app.schemas.species import SpeciesStrainCreateMixin, SpeciesStrainReadMixin
from app.schemas.utils import make_update_schema


class MEModelBaseMixin(NameDescriptionMixin):
    validation_status: ValidationStatus = ValidationStatus.created


# To be used by entities who reference MEModel
class NestedMEModel(MEModelBaseMixin, NestedEntityRead):
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None


class MEModelCreateFields(MEModelBaseMixin, SpeciesStrainCreateMixin, EntityCreate):
    brain_region_id: uuid.UUID
    morphology_id: uuid.UUID
    emodel_id: uuid.UUID


class MEModelCreate(
    MEModelCreateFields,
    MTypeClassIdsCreateMixin,
    ETypeClassIdsCreateMixin,
):
    pass


MEModelUserUpdate = make_update_schema(MEModelCreateFields, "MEModelUserUpdate")  # pyright: ignore [reportInvalidTypeForm]

MEModelAdminUpdate = make_update_schema(
    MEModelCreateFields,
    "MEModelAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class MEModelRead(
    MEModelBaseMixin,
    EntityReadWoutAssets,
    BrainRegionReadMixin,
    SpeciesStrainReadMixin,
):
    id: uuid.UUID
    mtypes: list[MTypeClassRead] | None
    etypes: list[ETypeClassRead] | None
    morphology: CellMorphologyRead
    emodel: EModelRead
    calibration_result: NestedMEModelCalibrationResultRead | None
