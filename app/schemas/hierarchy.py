"""Circuit hierarchy schemas."""

import uuid

from app.db.types import DerivationType
from app.schemas.base import Schema


class HierarchyNode(Schema):
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None
    children: list["HierarchyNode"] = []  # ruff:ignore[mutable-class-default]
    authorized_public: bool
    authorized_project_id: uuid.UUID


class HierarchyTree(Schema):
    derivation_type: DerivationType
    data: list[HierarchyNode]
