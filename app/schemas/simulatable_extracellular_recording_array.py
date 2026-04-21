import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import ElectrodeType
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    NameDescriptionMixin,
)
from app.schemas.contribution import ContributionReadWithoutEntityMixin
from app.schemas.utils import make_update_schema


class SimulatableExtracellularRecordingArrayBase(BaseModel, NameDescriptionMixin):
    model_config = ConfigDict(from_attributes=True)

    electrode_type: ElectrodeType
    circuit_id: uuid.UUID


class SimulatableExtracellularRecordingArrayCreate(
    SimulatableExtracellularRecordingArrayBase, AuthorizationOptionalPublicMixin
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
    SimulatableExtracellularRecordingArrayBase, EntityTypeMixin, IdentifiableMixin
):
    pass


class SimulatableExtracellularRecordingArrayRead(
    NestedSimulatableExtracellularRecordingArrayRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
    ContributionReadWithoutEntityMixin,
):
    pass
