"""Helpers to make sure queries are filtered to the allowed members."""

from typing import Any

from pydantic import UUID4
from sqlalchemy import Delete, Select, and_, false, not_, or_, select, true
from sqlalchemy.orm import Query

from app.db.model import Entity
from app.db.utils import get_declaring_class
from app.schemas.auth import UserContext


def constrain_to_accessible_entities[Q: Query | Select](
    query: Q,
    user_context: UserContext | None,
    db_model_class: Any = Entity,
) -> Q:
    """Ensure a query is filtered to rows that are viewable by the user."""
    if not user_context:  # admin or global resource
        return query

    # if model or alias has an authorized_project_id use it as is
    if hasattr(db_model_class, "authorized_project_id"):
        id_model_class = db_model_class
    # otherwise look up the hierarchy to check if there is one defined there
    else:
        id_model_class = get_declaring_class(db_model_class, "authorized_project_id")
        # global resource without authorized_project_id, always accessible
        if not id_model_class:
            return query

    # if user passes a specific project_id, use it to constrain resources
    if user_context.project_id:
        return query.where(
            or_(
                id_model_class.authorized_public == true(),
                id_model_class.authorized_project_id == user_context.project_id,
            )
        )

    # otherwise use user_project_ids from token to check if user has access
    return query.where(
        or_(
            id_model_class.authorized_public == true(),
            id_model_class.authorized_project_id.in_(user_context.user_project_ids),
        )
    )


def constrain_to_private_entities[Q: Query | Select](
    query: Q,
    user_context: UserContext,
    db_model_class: Any = Entity,
) -> Q:
    """Ensure a query is filtered to private rows that are viewable by the user."""
    # if user passes a specific project_id, use it to constrain resources
    if user_context.project_id:
        return query.where(
            and_(
                db_model_class.authorized_public == false(),
                db_model_class.authorized_project_id == user_context.project_id,
            )
        )

    # otherwise use project_ids from token to check if user has access
    return query.where(
        and_(
            db_model_class.authorized_public == false(),
            db_model_class.authorized_project_id.in_(user_context.user_project_ids),
        )
    )


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
