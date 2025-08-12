import uuid

from pydantic import BaseModel, ConfigDict, HttpUrl, AnyUrl

from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead
from app.db.types import EmMeshType, EmMeshGenerationMethod


class EMDenseReconstructionDatasetBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    protocol: HttpUrl | None = None
    fixation: str | None = None
    staining: str | None = None  # TODO: controlled vocabulary
    slicing: float | None = None
    shrinkage: float | None = None
    microscope_type: str | None = None  # TODO: controlled vocabulary
    detector: str | None = None
    orientation: str | None = None
    landmarks: str | None = None
    voltage : float | None = None
    current: float | None = None
    dose: float | None = None
    temperature: float | None = None

    volume_resolution_x_nm: float
    volume_resolution_y_nm: float
    volume_resolution_z_nm: float
    release_url: HttpUrl
    cave_client_url: AnyUrl
    cave_datastack: str
    precomputed_mesh_url: AnyUrl | None = None
    cell_identifying_property: str = "pt_root_id"

class EMDenseReconstructionDatasetRead(EMDenseReconstructionDatasetBase, ScientificArtifactRead):
    pass

class EMDenseReconstructionDatasetCreate(EMDenseReconstructionDatasetBase, ScientificArtifactCreate):
    pass

class EMCellMeshBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    relase_version: int
    dense_reconstruction_cell_id: int
    generation_method: EmMeshGenerationMethod
    level_of_detail: int
    generation_parameters: str | None = None
    mesh_type : EmMeshType

class EMCellMeshRead(EMCellMeshBase, ScientificArtifactRead):
    em_release: EMDenseReconstructionDatasetRead

class EMCellMeshCreate(EMCellMeshBase, ScientificArtifactCreate):
    em_release_id: uuid.UUID | None = None
