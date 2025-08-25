from pydantic import BaseModel

from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead
from app.schemas.types import SerializableAnyUrl, SerializableHttpUrl


class EMDenseReconstructionDatasetBase(BaseModel):
    name: str
    description: str

    protocol: SerializableHttpUrl | None = None
    fixation: str | None = None
    staining: str | None = None  # TODO: controlled vocabulary
    slicing: float | None = None
    shrinkage: float | None = None
    microscope_type: str | None = None  # TODO: controlled vocabulary
    detector: str | None = None
    orientation: str | None = None
    landmarks: str | None = None
    voltage: float | None = None
    current: float | None = None
    dose: float | None = None
    temperature: float | None = None

    volume_resolution_x_nm: float
    volume_resolution_y_nm: float
    volume_resolution_z_nm: float
    release_url: SerializableHttpUrl
    cave_client_url: SerializableAnyUrl
    cave_datastack: str
    precomputed_mesh_url: SerializableAnyUrl
    cell_identifying_property: str


class EMDenseReconstructionDatasetRead(
    EMDenseReconstructionDatasetBase,
    ScientificArtifactRead,
):
    pass


class EMDenseReconstructionDatasetCreate(
    EMDenseReconstructionDatasetBase,
    ScientificArtifactCreate,
):
    pass
