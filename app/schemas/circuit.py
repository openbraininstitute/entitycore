import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import CircuitBuildCategory, CircuitScale
from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead
from app.schemas.utils import make_update_schema


class CircuitBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str

    has_morphologies: bool = False
    has_point_neurons: bool = False
    has_electrical_cell_models: bool = False
    has_spines: bool = False

    number_neurons: int
    number_synapses: int
    number_connections: int | None

    scale: CircuitScale
    build_category: CircuitBuildCategory

    root_circuit_id: uuid.UUID | None = None
    atlas_id: uuid.UUID | None = None


class CircuitRead(CircuitBase, ScientificArtifactRead):
    pass


class CircuitCreate(CircuitBase, ScientificArtifactCreate):
    pass


CircuitUserUpdate = make_update_schema(CircuitCreate, "CircuitUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
CircuitAdminUpdate = make_update_schema(
    CircuitCreate,
    "CircuitAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
