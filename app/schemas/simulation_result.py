import uuid

from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.utils import make_update_schema


class SimulationResultBaseMixin(NameDescriptionMixin):
    simulation_id: uuid.UUID


class SimulationResultCreate(SimulationResultBaseMixin, EntityCreate):
    pass


SimulationResultUserUpdate = make_update_schema(
    SimulationResultCreate, "SimulationResultUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
SimulationResultAdminUpdate = make_update_schema(
    SimulationResultCreate,
    "SimulationResultAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedSimulationResultRead(SimulationResultBaseMixin, NestedEntityRead):
    pass


class SimulationResultRead(
    SimulationResultBaseMixin,
    EntityRead,
):
    pass
