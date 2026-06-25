import uuid

from app.db.types import CircuitBuildCategory, CircuitScale, DerivationType, TargetSimulator
from app.schemas.base import NameDescriptionMixin, Schema
from app.schemas.entity import NestedEntityRead
from app.schemas.scientific_artifact import ScientificArtifactCreate, ScientificArtifactRead
from app.schemas.utils import make_update_schema


class CircuitBaseMixin(NameDescriptionMixin):
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
    target_simulator: TargetSimulator = TargetSimulator.neuron


class CircuitRead(CircuitBaseMixin, ScientificArtifactRead):
    pass


class CircuitGeneratedDerivationRead(Schema):
    """A derivation where the circuit is the generated (derived) entity."""

    used: NestedEntityRead
    derivation_type: DerivationType
    label: str | None = None


class CircuitUsedDerivationRead(Schema):
    """A derivation where the circuit is the used (source) entity."""

    generated: NestedEntityRead
    derivation_type: DerivationType
    label: str | None = None


class CircuitExpandedRead(CircuitRead):
    """Circuit read schema with on-demand derivation lists (see `expand` query param).

    A direction that was not expanded serializes as ``null`` (load-aware property on the model).
    """

    generated_derivations: list[CircuitGeneratedDerivationRead] | None = None
    used_derivations: list[CircuitUsedDerivationRead] | None = None


class CircuitCreate(CircuitBaseMixin, ScientificArtifactCreate):
    pass


CircuitUserUpdate = make_update_schema(CircuitCreate, "CircuitUserUpdate")  # pyright: ignore [reportInvalidTypeForm]
CircuitAdminUpdate = make_update_schema(
    CircuitCreate,
    "CircuitAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
