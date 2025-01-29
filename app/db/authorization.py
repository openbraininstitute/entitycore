"""Helpers to make sure queries are filtered to the allowed members"""

from fastapi import Request
from pydantic import UUID4
from sqlalchemy import or_
from sqlalchemy.orm import Query

from app.db.model import Entity


def raise_if_unauthorized(request: Request, project_id: UUID4):
    # XXX: this needs to call the virtualab-api, and check if the user is part
    # of the lab/project that they claim they are writing too
    #raise Exception("Unauthorized project_id: {project_id} for user {user}")
    pass


def constrain_query_to_members(query: Query, project_id: UUID4):
    """Ensure a query is filtered to rows that are viewable by the user"""
    query = query.filter(
        or_(
            Entity.authorized_public == True,
            Entity.authorized_project_id == project_id,
        )
    )

    return query
