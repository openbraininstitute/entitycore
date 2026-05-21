"""Helpers to make sure queries are filtered to the allowed members."""

from typing import Protocol
from uuid import UUID

from pydantic import UUID4
from sqlalchemy import (
    Delete,
    Select,
    SQLColumnExpression,
    and_,
    false,
    not_,
    or_,
    select,
    true,
)
from sqlalchemy.orm import Mapped, Query

from app.db.model import Entity
from app.schemas.auth import UserContext


class HasId(Protocol):
    id: Mapped[UUID]


class HasAuth(Protocol):
    authorized_project_id: Mapped[UUID]
    authorized_public: Mapped[bool]


def is_public(model: type[HasAuth]) -> SQLColumnExpression[bool]:
    return model.authorized_public == true()


def is_private(model: type[HasAuth]) -> SQLColumnExpression[bool]:
    return model.authorized_public == false()


def is_in_projects(model: type[HasAuth], project_ids: list[UUID4]) -> SQLColumnExpression[bool]:
    return model.authorized_project_id.in_(project_ids) if project_ids else false()


def is_public_or_in_projects(
    model: type[HasAuth], project_ids: list[UUID4]
) -> SQLColumnExpression[bool]:
    return or_(is_public(model), is_in_projects(model, project_ids))


def is_private_and_in_projects(
    model: type[HasAuth], project_ids: list[UUID4]
) -> SQLColumnExpression[bool]:
    return and_(is_private(model), is_in_projects(model, project_ids))


def is_in_ids(model: type[HasId], ids: list[UUID4]) -> SQLColumnExpression[bool]:
    return model.id.in_(ids) if ids else false()


def is_writable_by_user(
    *,
    model: type[HasAuth],
    project_ids: list[UUID4],
    is_service_maintainer: bool,
) -> SQLColumnExpression[bool]:
    if is_service_maintainer:
        return is_in_projects(model, project_ids)

    return is_private_and_in_projects(model, project_ids)


def constrain_to_writable_entities[Q: Query | Select](
    *,
    query: Q,
    user_context: UserContext,
    db_model_class: type[HasAuth] = Entity,
) -> Q:
    """Constrain query to writable entities.

    Permisions:
    - Service maintainers have write access to all the entities in the allowed projects
    - Admins are not handled by this function and will be treated as regular users

    Note:
        A project_id context has precedence over Keycloak-derived project ids.
        If one is provided query will be constrained within that single project_id.
    """
    return query.where(
        is_writable_by_user(
            model=db_model_class,
            project_ids=user_context.authorized_project_ids,
            is_service_maintainer=user_context.is_service_maintainer,
        )
    )


def constrain_to_accessible_entities[Q: Query | Select](
    *,
    query: Q,
    user_context: UserContext,
    db_model_class: type[HasAuth] = Entity,
) -> Q:
    """Ensure a query is filtered to rows that are viewable by the user.

    TODO: Consolidate with constrain_to_readable_entities and adapt read_many calls
    """
    return query.where(
        is_public_or_in_projects(db_model_class, user_context.authorized_project_ids)
    )


def constrain_to_readable_entities[Q: Query | Select](
    *,
    query: Q,
    project_id: UUID4 | None,
    db_model_class: type[HasAuth] = Entity,
) -> Q:
    """Ensure a query is filtered to rows that are viewable by the user."""
    if project_id is None:
        return query.where(is_public(db_model_class))

    return query.where(is_public_or_in_projects(db_model_class, [project_id]))


def constrain_to_private_entities[Q: Query | Select](
    *,
    query: Q,
    user_context: UserContext,
    db_model_class: type[HasAuth] = Entity,
) -> Q:
    """Ensure a query is filtered to private rows that are viewable by the user."""
    return query.where(is_private_and_in_projects(db_model_class, user_context.user_project_ids))


def constrain_entity_query_to_project[Q: Query | Select | Delete](
    *, query: Q, project_id: UUID4
) -> Q:
    """Ensure a query is filtered to rows in the user's project."""
    return query.where(is_in_projects(Entity, [project_id]))


def select_unauthorized_entities(*, ids: list[UUID4], project_id: UUID4 | None) -> Select:
    model = Entity
    is_authorized = (
        is_public(model) if project_id is None else is_public_or_in_projects(model, [project_id])
    )
    return select(model.id).where(
        is_in_ids(model, ids),
        not_(is_authorized),
    )
