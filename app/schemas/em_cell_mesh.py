import uuid
from typing import Any

from pydantic import BaseModel

from app.db.types import EMCellMeshGenerationMethod, EMCellMeshType
from app.schemas.base import BasicEntityRead
from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead


class EMCellMeshBase(BaseModel):
    release_version: int
    dense_reconstruction_cell_id: int
    generation_method: EMCellMeshGenerationMethod
    level_of_detail: int
    generation_parameters: dict[str, Any] | None = None
    mesh_type: EMCellMeshType


class EMCellMeshRead(
    EMCellMeshBase,
    ScientificArtifactRead,
):
    em_dense_reconstruction_dataset: BasicEntityRead


class EMCellMeshCreate(
    EMCellMeshBase,
    ScientificArtifactCreate,
):
    em_dense_reconstruction_dataset_id: uuid.UUID
