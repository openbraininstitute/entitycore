"""Helpers to make sure queries are filtered to the allowed members."""

from pydantic import UUID4
from sqlalchemy import Select, false, or_, true
from sqlalchemy.orm import Query

from app.db.model import Entity


def constrain_to_accessible_entities(query: Query | Select, project_id: UUID4 | None):
    """Ensure a query is filtered to rows that are viewable by the user."""
    query = query.where(
        or_(
            Entity.authorized_public == true(),
            Entity.authorized_project_id == project_id if project_id else false(),
        )
    )

    return query


def constrain_entity_query_to_project(query: Query | Select, project_id: UUID4):
    """Ensure a query is filtered to rows in the user's project."""
    return query.where(Entity.authorized_project_id == project_id)
