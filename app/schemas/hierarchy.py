"""Circuit hierarchy schemas."""

import uuid

from pydantic import BaseModel

from app.db.types import DerivationType


class HierarchyNode(BaseModel):
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None
    children: list["HierarchyNode"] = []
    authorized_public: bool
    authorized_project_id: uuid.UUID


class HierarchyTree(BaseModel):
    derivation_type: DerivationType
    data: list[HierarchyNode]
