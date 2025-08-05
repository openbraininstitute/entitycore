"""Circuit hierarchy schemas."""

import uuid

from pydantic import BaseModel

from app.db.types import DerivationType


class CircuitNode(BaseModel):
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None
    derivation_type: DerivationType | None
    children: list["CircuitNode"] = []


class CircuitHierarchy(BaseModel):
    data: list[CircuitNode]
