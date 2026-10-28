import uuid

from app.db.types import (
    PointLocationBase,
    RepairPipelineType,
)
from app.schemas.annotation import MTypeClassRead
from app.schemas.base import NameDescriptionMixin
from app.schemas.cell_morphology_protocol import NestedCellMorphologyProtocolRead
from app.schemas.measurement_annotation import MeasurementAnnotationRead
from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead
from app.schemas.utils import make_update_schema


class CellMorphologyBaseMixin(NameDescriptionMixin):
    location: PointLocationBase | None
    legacy_id: list[str] | None = None
    has_segmented_spines: bool = False
    repair_pipeline_state: RepairPipelineType | None = None


class CellMorphologyCreate(
    CellMorphologyBaseMixin,
    ScientificArtifactCreate,
):
    subject_id: uuid.UUID
    brain_region_id: uuid.UUID
    cell_morphology_protocol_id: uuid.UUID


CellMorphologyUserUpdate = make_update_schema(CellMorphologyCreate, "CellMorphologyUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
CellMorphologyAdminUpdate = make_update_schema(
    CellMorphologyCreate,
    "CellMorphologyAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class CellMorphologyRead(
    CellMorphologyBaseMixin,
    ScientificArtifactRead,
):
    mtypes: list[MTypeClassRead] | None
    cell_morphology_protocol: NestedCellMorphologyProtocolRead


class CellMorphologyAnnotationExpandedRead(CellMorphologyRead):
    measurement_annotation: MeasurementAnnotationRead | None
