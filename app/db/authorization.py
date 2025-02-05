"""Helpers to make sure queries are filtered to the allowed members."""

from pydantic import UUID4
from sqlalchemy import or_
from sqlalchemy.orm import Query

from app.db.model import Entity


def constrain_query_to_members(query: Query, project_id: UUID4):
    """Ensure a query is filtered to rows that are viewable by the user."""
    query = query.filter(
        or_(
            Entity.authorized_public,
            Entity.authorized_project_id == project_id,
        )
    )

    return query
