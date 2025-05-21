import uuid

from pydantic import BaseModel

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.base import (
    CreationMixin,
    IdentifiableMixin,
)


class CalibrationResultBase(BaseModel):
    name: str
    description: str
    value: float
    calibrated_entity_id: uuid.UUID


class CalibrationResultRead(
    CalibrationResultBase, CreationMixin, IdentifiableMixin, CreatedByUpdatedByMixin
):
    pass


class CalibrationResultCreate(CalibrationResultBase):
    pass
