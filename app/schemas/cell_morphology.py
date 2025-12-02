import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import (
    PointLocationBase,
)
from app.schemas.annotation import MTypeClassRead
from app.schemas.cell_morphology_protocol import NestedCellMorphologyProtocolRead
from app.schemas.measurement_annotation import MeasurementAnnotationRead
from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead
from app.schemas.utils import make_update_schema


class CellMorphologyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    location: PointLocationBase | None
    legacy_id: list[str] | None = None
    has_segmented_spines: bool = False


class CellMorphologyCreate(
    CellMorphologyBase,
    ScientificArtifactCreate,
):
    subject_id: uuid.UUID
    brain_region_id: uuid.UUID
    cell_morphology_protocol_id: uuid.UUID | None = None


CellMorphologyUserUpdate = make_update_schema(CellMorphologyCreate, "CellMorphologyUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
CellMorphologyAdminUpdate = make_update_schema(
    CellMorphologyCreate,
    "CellMorphologyAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class CellMorphologyRead(
    CellMorphologyBase,
    ScientificArtifactRead,
):
    mtypes: list[MTypeClassRead] | None
    cell_morphology_protocol: NestedCellMorphologyProtocolRead | None


class CellMorphologyAnnotationExpandedRead(CellMorphologyRead):
    measurement_annotation: MeasurementAnnotationRead | None
