import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import CircuitBuildCategory, CircuitScale
from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead


class CircuitBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    has_morphologies: bool
    has_point_neruons: bool
    has_electrical_cell_models: bool
    has_spines: bool

    number_neurons: int
    number_synapses: int
    number_connections: int | None

    scale: CircuitScale
    build_category: CircuitBuildCategory


class CircuitRead(CircuitBase, ScientificArtifactRead):
    pass


class CircuitCreate(CircuitBase, ScientificArtifactCreate):
    root_circuit_id: uuid.UUID | None = None
    atlas_id: uuid.UUID | None = None
