"""Helpers to make sure queries are filtered to the allowed members."""

from typing import Any

from pydantic import UUID4
from sqlalchemy import Delete, Select, and_, false, not_, or_, select, true
from sqlalchemy.orm import DeclarativeBase, Query

from app.db.model import Entity


def constrain_to_accessible_entities[T: DeclarativeBase](
    query: Select[tuple[T]],
    project_id: UUID4 | None,
    db_model_class: Any = Entity,
):
    """Ensure a query is filtered to rows that are viewable by the user."""
    query = query.where(
        or_(
            db_model_class.authorized_public == true(),
            db_model_class.authorized_project_id == project_id if project_id else false(),
        )
    )

    return query


def constrain_entity_query_to_project[Q: Query | Select | Delete](query: Q, project_id: UUID4) -> Q:
    """Ensure a query is filtered to rows in the user's project."""
    return query.where(Entity.authorized_project_id == project_id)


def select_unauthorized_entities(ids: list[UUID4], project_id: UUID4 | None) -> Select:
    return select(Entity.id).where(
        and_(
            Entity.id.in_(ids),
            not_(
                or_(
                    Entity.authorized_public == true(),
                    Entity.authorized_project_id == project_id if project_id else false(),
                ),
            ),
        )
    )
