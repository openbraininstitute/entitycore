import uuid
from collections import Counter

import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.orm import Session, aliased

from app.db.auth import constrain_to_accessible_entities
from app.db.model import Circuit, Derivation, Entity
from app.db.types import DerivationType
from app.dependencies.auth import UserContextDep
from app.dependencies.db import SessionDep
from app.logger import L
from app.schemas.auth import UserContext
from app.schemas.hierarchy import HierarchyNode, HierarchyTree


def _load_nodes(
    db: Session,
    user_context: UserContext,
    entity_class: type[Entity],
    derivation_type: DerivationType,
) -> dict[uuid.UUID, HierarchyNode]:
    root = aliased(entity_class, flat=True, name="root")
    parent = aliased(entity_class, flat=True, name="parent")
    child = aliased(entity_class, flat=True, name="child")
    order_by = ["name", "id"]
    matching_derivation_for_root = sa.select(sa.literal(1)).where(
        Derivation.generated_id == root.id,
        Derivation.derivation_type == derivation_type,
    )
    query_roots = (
        sa.select(
            root.id,
            getattr(root, "name", sa.literal(None)).label("name"),
            sa.literal(None).label("parent_id"),
            root.authorized_public,
            root.authorized_project_id,
        )
        .where(~sa.exists(matching_derivation_for_root))
        .order_by(*order_by)
    )
    query_roots = constrain_to_accessible_entities(
        query_roots, user_context=user_context, db_model_class=root
    )
    query_children = (
        sa.select(
            child.id,
            getattr(child, "name", sa.literal(None)).label("name"),
            parent.id.label("parent_id"),
            child.authorized_public,
            child.authorized_project_id,
        )
        .select_from(Derivation)
        .join(parent, parent.id == Derivation.used_id)
        .join(child, child.id == Derivation.generated_id)
        .where(Derivation.derivation_type == derivation_type)
        .order_by(*order_by)
    )
    query_children = constrain_to_accessible_entities(
        query_children, user_context=user_context, db_model_class=parent
    )
    query_children = constrain_to_accessible_entities(
        query_children, user_context=user_context, db_model_class=child
    )
    query = query_roots.union_all(query_children)

    rows = db.execute(query).all()
    all_nodes = {
        row.id: HierarchyNode(
            id=row.id,
            name=row.name,
            parent_id=row.parent_id,
            authorized_public=row.authorized_public,
            authorized_project_id=row.authorized_project_id,
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
    derivation_type: DerivationType,
) -> HierarchyTree:
    """Return a hierarchy tree of circuits based on derivations.

    Depending on the derivation type, the hierarchy will be built differently. In particular,
    a circuit is considered a root if it has no parents of the specified derivation type.

    The hierarchy assumes the following rules for the derivations:

    - A circuit can have zero or more children linked with any derivation type.
    - A circuit can have zero or more parents, provided each parent is different, and is linked with
      a different derivation type.
    - A public circuit can have any combination of public and private circuits as children.
    - A private circuit can have only private circuits with the same project_id as children.

    See also https://github.com/openbraininstitute/entitycore/issues/292#issuecomment-3174884561
    """
    all_nodes = _load_nodes(
        db,
        user_context=user_context,
        entity_class=Circuit,
        derivation_type=derivation_type,
    )
    root_nodes: list[HierarchyNode] = []
    for node in all_nodes.values():
        if node.parent_id is None:
            root_nodes.append(node)
        else:
            parent = all_nodes[node.parent_id]
            parent.children.append(node)
    return HierarchyTree(
        derivation_type=derivation_type,
        data=root_nodes,
    )
