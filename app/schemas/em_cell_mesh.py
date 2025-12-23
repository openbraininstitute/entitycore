import uuid
from typing import Any

from pydantic import BaseModel

from app.db.types import EMCellMeshGenerationMethod, EMCellMeshType
from app.schemas.annotation import MTypeClassRead
from app.schemas.base import BasicEntityRead
from app.schemas.measurement_annotation import MeasurementAnnotationRead
from app.schemas.scientific_artifact import (
    NestedScientificArtifactRead,
    ScientificArtifactCreate,
    ScientificArtifactRead,
)
from app.schemas.utils import make_update_schema


class EMCellMeshBase(BaseModel):
    release_version: int
    dense_reconstruction_cell_id: int
    generation_method: EMCellMeshGenerationMethod
    level_of_detail: int
    generation_parameters: dict[str, Any] | None = None
    mesh_type: EMCellMeshType


class NestedEMCellMeshRead(
    EMCellMeshBase,
    NestedScientificArtifactRead,
):
    pass


class EMCellMeshRead(
    EMCellMeshBase,
    ScientificArtifactRead,
):
    em_dense_reconstruction_dataset: BasicEntityRead
    mtypes: list[MTypeClassRead] | None


class EMCellMeshCreate(
    EMCellMeshBase,
    ScientificArtifactCreate,
):
    em_dense_reconstruction_dataset_id: uuid.UUID


EMCellMeshUserUpdate = make_update_schema(
    EMCellMeshCreate, "EMCellMeshUserUpdate"
)  # pyright : ignore [reportInvalidTypeForm]


class EMCellMeshAnnotationExpandedRead(EMCellMeshRead):
    measurement_annotation: MeasurementAnnotationRead | None
