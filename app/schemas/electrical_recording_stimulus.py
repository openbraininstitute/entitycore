import uuid

from pydantic import BaseModel

from app.db.types import (
    ElectricalRecordingStimulusShape,
    ElectricalRecordingStimulusType,
)
from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
    NameDescriptionMixin,
)
from app.schemas.utils import make_update_schema


class ElectricalRecordingStimulusBase(BaseModel, NameDescriptionMixin):
    dt: float | None = None
    injection_type: ElectricalRecordingStimulusType
    shape: ElectricalRecordingStimulusShape
    start_time: float | None = None
    end_time: float | None = None
    recording_id: uuid.UUID


class NestedElectricalRecordingStimulusRead(
    ElectricalRecordingStimulusBase, IdentifiableMixin, EntityTypeMixin
):
    pass


class ElectricalRecordingStimulusRead(
    NestedElectricalRecordingStimulusRead,
    CreationMixin,
    CreatedByUpdatedByMixin,
    AuthorizationMixin,
):
    pass


class ElectricalRecordingStimulusCreate(
    ElectricalRecordingStimulusBase, AuthorizationOptionalPublicMixin
):
    pass


ElectricalRecordingStimulusUserUpdate = make_update_schema(
    ElectricalRecordingStimulusCreate, "ElectricalRecordingStimulusUserUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
ElectricalRecordingStimulusAdminUpdate = make_update_schema(
    ElectricalRecordingStimulusCreate,
    "ElectricalRecordingStimulusAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]
