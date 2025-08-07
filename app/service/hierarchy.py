import uuid
from collections import Counter

import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.orm import Session, aliased

from app.db.auth import constrain_to_accessible_entities
from app.db.model import Circuit, Derivation, Entity
from app.dependencies.auth import UserContextDep
from app.dependencies.db import SessionDep
from app.logger import L
from app.schemas.hierarchy import HierarchyNode, HierarchyTree


def _load_nodes(
    db: Session,
    project_id: uuid.UUID | None,
    entity_class: type[Entity],
) -> dict[uuid.UUID, HierarchyNode]:
    root = aliased(entity_class, flat=True, name="root")
    parent = aliased(entity_class, flat=True, name="parent")
    child = aliased(entity_class, flat=True, name="child")
    order_by = ["name", "id"]
    subq = sa.select(sa.literal(1)).where(
        Derivation.generated_id == root.id,
    )
    query_roots = (
        sa.select(
            root.id,
            getattr(root, "name", sa.literal(None)).label("name"),
            sa.literal(None).label("parent_id"),
            sa.literal(None).label("derivation_type"),
        )
        .where(~sa.exists(subq))
        .order_by(*order_by)
    )
    query_roots = constrain_to_accessible_entities(
        query_roots, project_id=project_id, db_model_class=root
    )
    query_children = (
        sa.select(
            child.id,
            getattr(child, "name", sa.literal(None)).label("name"),
            parent.id.label("parent_id"),
            Derivation.derivation_type,
        )
        .select_from(Derivation)
        .join(parent, parent.id == Derivation.used_id)
        .join(child, child.id == Derivation.generated_id)
        .order_by(*order_by)
    )
    query_children = constrain_to_accessible_entities(
        query_children, project_id=project_id, db_model_class=parent
    )
    query_children = constrain_to_accessible_entities(
        query_children, project_id=project_id, db_model_class=child
    )
    query = query_roots.union_all(query_children)

    rows = db.execute(query).all()
    all_nodes = {
        row.id: HierarchyNode(
            id=row.id,
            name=row.name,
            parent_id=row.parent_id,
            derivation_type=row.derivation_type,
        )
        for row in rows
    }
    if len(rows) != len(all_nodes):
        counter = Counter(row.id for row in rows)
        ids = sorted(k for k, v in counter.items() if v > 1)
        L.warning("Inconsistent hierarchy, entities with multiple parents: {}", ids)
        raise HTTPException(status_code=500, detail="Inconsistent hierarchy.")
    return all_nodes


def read_circuit_hierarchy(
    user_context: UserContextDep,
    db: SessionDep,
) -> HierarchyTree:
    """Return the circuit hierarchy based on derivations."""
    all_nodes = _load_nodes(db, project_id=user_context.project_id, entity_class=Circuit)
    root_nodes: list[HierarchyNode] = []
    for node in all_nodes.values():
        if node.parent_id is None:
            root_nodes.append(node)
        else:
            parent = all_nodes[node.parent_id]
            parent.children.append(node)
    return HierarchyTree(data=root_nodes)
