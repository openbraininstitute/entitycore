"""Circuit hierarchy schemas."""

import uuid

from pydantic import BaseModel

from app.db.types import DerivationType


class HierarchyNode(BaseModel):
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None
    children: list["HierarchyNode"] = []


class HierarchyTree(BaseModel):
    derivation_type: DerivationType
    data: list[HierarchyNode]
