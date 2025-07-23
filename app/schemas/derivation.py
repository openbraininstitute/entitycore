import uuid

from pydantic import BaseModel, ConfigDict

from app.db.types import DerivationType
from app.schemas.base import BasicEntityRead


class DerivationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DerivationCreate(DerivationBase):
    used_id: uuid.UUID
    generated_id: uuid.UUID
    derivation_type: DerivationType | None = None


class DerivationRead(DerivationBase):
    used: BasicEntityRead
    generated: BasicEntityRead
    derivation_type: DerivationType | None = None
