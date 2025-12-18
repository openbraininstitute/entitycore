"""Helpers to make sure queries are filtered to the allowed members."""

from typing import Any

from pydantic import UUID4
from sqlalchemy import Delete, Select, and_, false, not_, or_, select, true
from sqlalchemy.orm import Query, Session

from app.config import settings
from app.db.model import Entity, Identifiable
from app.queries.utils import get_user
from app.schemas.auth import UserContext


def constrain_to_writable_entities[Q: Query | Select](
    query: Q,
    user_context: UserContext,
    db_model_class: Any = Entity,
) -> Q:
    """Constrain query to writable entities.

    Permisions:
    - Service maintainers have write access to all the entities in the allowed projects
    - Admins are not handled by this function and will be treated as regular users

    Note:
        A project_id context has precedence over Keycloak-derived project ids.
        If one is provided query will be constrained within that single project_id.
    """
    project_ids = (
        [user_context.project_id] if user_context.project_id else user_context.user_project_ids
    )

    if user_context.is_service_maintainer:
        return query.where(
            db_model_class.authorized_project_id.in_(project_ids),
        )

    return query.where(
        and_(
            db_model_class.authorized_public == false(),
            db_model_class.authorized_project_id.in_(project_ids),
        )
    )


def constrain_to_accessible_entities[Q: Query | Select](
    query: Q,
    project_id: UUID4 | None,
    db_model_class: Any = Entity,
) -> Q:
    """Ensure a query is filtered to rows that are viewable by the user."""
    query = query.where(
        or_(
            db_model_class.authorized_public == true(),
            db_model_class.authorized_project_id == project_id if project_id else false(),
        )
    )

    return query


def constrain_to_private_entities[Q: Query | Select](
    query: Q,
    user_context: UserContext,
    db_model_class: Any = Entity,
) -> Q:
    """Ensure a query is filtered to private rows that are viewable by the user."""
    return query.where(
        and_(
            db_model_class.authorized_public == false(),
            db_model_class.authorized_project_id.in_(user_context.user_project_ids)
            if user_context.user_project_ids
            else false(),
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


def is_user_authorized_for_deletion(  # noqa: PLR0911
    db: Session, user_context: UserContext, obj: Identifiable
) -> bool:
    if settings.APP_DISABLE_AUTH:
        return True

    # if there is no authorized_project_id it is a global resource
    if not (project_id := getattr(obj, "authorized_project_id", None)):
        return False

    # Service maintainers may delete public/private entities within their projects.
    if user_context.is_service_maintainer:
        return project_id in user_context.user_project_ids

    # from here and below public entities cannot be deleted
    if obj.authorized_public:  # pyright: ignore [reportAttributeAccessIssue]
        return False

    # Project admins may delete private entities within their projects
    if project_id in user_context.admin_project_ids:
        return True

    # Project members may delete only the private entities they themselves created
    if project_id in user_context.member_project_ids and (
        db_user := get_user(db, user_context.profile.subject)
    ):
        return db_user.created_by_id == obj.created_by_id

    return False
