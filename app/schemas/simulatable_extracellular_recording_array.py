import uuid

from app.db.types import ElectrodeType
from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.utils import make_update_schema


class SimulatableExtracellularRecordingArrayBaseMixin(NameDescriptionMixin):
    electrode_type: ElectrodeType
    circuit_id: uuid.UUID


class SimulatableExtracellularRecordingArrayCreate(
    SimulatableExtracellularRecordingArrayBaseMixin, EntityCreate
):
    pass


SimulatableExtracellularRecordingArrayUserUpdate = make_update_schema(
    SimulatableExtracellularRecordingArrayCreate, "SimulatableExtracellularRecordingArrayUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
SimulatableExtracellularRecordingArrayAdminUpdate = make_update_schema(
    SimulatableExtracellularRecordingArrayCreate,
    "SimulatableExtracellularRecordingArrayAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedSimulatableExtracellularRecordingArrayRead(
    SimulatableExtracellularRecordingArrayBaseMixin,
    NestedEntityRead,
):
    pass


class SimulatableExtracellularRecordingArrayRead(
    SimulatableExtracellularRecordingArrayBaseMixin,
    EntityRead,
):
    pass
