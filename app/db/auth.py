"""Helpers to make sure queries are filtered to the allowed members."""

from typing import Any

from pydantic import UUID4
from sqlalchemy import Delete, Select, false, or_, true
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
