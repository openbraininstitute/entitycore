from pydantic import BaseModel

from app.db.types import SlicingDirectionType
from app.schemas.base import NameDescriptionMixin
from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead
from app.schemas.types import SerializableAnyUrl, SerializableHttpUrl


class EMDenseReconstructionDatasetBase(BaseModel, NameDescriptionMixin):
    protocol_document: SerializableHttpUrl | None = None
    fixation: str | None = None
    staining_type: str | None = None  # TODO: controlled vocabulary
    slicing_thickness: float | None = None
    tissue_shrinkage: float | None = None
    microscope_type: str | None = None  # TODO: controlled vocabulary
    detector: str | None = None
    slicing_direction: SlicingDirectionType | None = None
    landmarks: str | None = None
    voltage: float | None = None
    current: float | None = None
    dose: float | None = None
    temperature: float | None = None

    volume_resolution_x_nm: float
    volume_resolution_y_nm: float
    volume_resolution_z_nm: float
    release_url: SerializableHttpUrl | None = None
    cave_client_url: SerializableAnyUrl | None = None
    cave_datastack: str | None = None
    precomputed_mesh_url: SerializableAnyUrl | None = None
    cell_identifying_property: str | None = None


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
