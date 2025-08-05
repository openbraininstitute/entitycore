import uuid
from collections import Counter

import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.orm import Session, aliased

from app.db.auth import constrain_to_accessible_entities
from app.db.model import Circuit, Derivation
from app.dependencies.auth import UserContextDep
from app.dependencies.db import SessionDep
from app.logger import L
from app.schemas.circuit_hierarchy import CircuitHierarchy, CircuitNode


def _load_circuit_nodes(
    db: Session,
    project_id: uuid.UUID | None,
) -> dict[uuid.UUID, CircuitNode]:
    root = aliased(Circuit, flat=True, name="root")
    parent = aliased(Circuit, flat=True, name="parent")
    child = aliased(Circuit, flat=True, name="child")
    query_roots = (
        sa.select(
            root.id,
            root.name,
            sa.literal(None).label("parent_id"),
            sa.literal(None).label("derivation_type"),
        )
        .where(root.root_circuit_id.is_(None))
        .order_by(root.name, root.id)
    )
    query_roots = constrain_to_accessible_entities(
        query_roots, project_id=project_id, db_model_class=root
    )
    query_children = (
        sa.select(
            child.id,
            child.name,
            parent.id.label("parent_id"),
            Derivation.derivation_type,
        )
        .select_from(Derivation)
        .join(parent, parent.id == Derivation.used_id)
        .join(child, child.id == Derivation.generated_id)
        .order_by(child.name, child.id)
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
        row.id: CircuitNode(
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
        L.warning("Inconsistent circuit hierarchy, circuits with multiple parents: {}", ids)
        raise HTTPException(status_code=500, detail="Inconsistent circuit hierarchy.")
    return all_nodes


def read_structure(
    user_context: UserContextDep,
    db: SessionDep,
) -> CircuitHierarchy:
    """Read the circuits and return the resulting hierarchy."""
    all_nodes = _load_circuit_nodes(db, project_id=user_context.project_id)
    root_nodes = {}
    for node in all_nodes.values():
        if node.parent_id is None:
            root_nodes[node.id] = node
        else:
            parent = all_nodes[node.parent_id]
            parent.children.append(node)
    return CircuitHierarchy(
        data=list(root_nodes.values()),
    )
