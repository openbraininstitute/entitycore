import uuid
from http import HTTPStatus

import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.orm import aliased, joinedload, raiseload

import app.queries.common
from app.db.auth import (
    constrain_entity_query_to_project,
    constrain_to_readable_entities,
    constrain_to_writable_entities,
)
from app.db.model import Agent, Contribution, Entity, Person
from app.dependencies.auth import AdminContextDep, UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ApiError, ApiErrorCode, ensure_result
from app.filters.contribution import ContributionFilterDep
from app.logger import L
from app.queries import crud
from app.queries.factory import query_params_factory
from app.queries.utils import is_user_authorized_for_deletion
from app.schemas.contribution import (
    ContributionAdminUpdate,
    ContributionCreate,
    ContributionRead,
    ContributionUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.join(Contribution.entity).options(
        joinedload(Contribution.agent),
        joinedload(Contribution.created_by),
        joinedload(Contribution.updated_by),
        joinedload(Contribution.entity),
        joinedload(Contribution.role),
        raiseload("*"),
    )


def _read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    filter_model: ContributionFilterDep,
    pagination_request: PaginationQuery,
    check_authorized_project: bool,
) -> ListResponse[ContributionRead]:
    agent_alias = aliased(Agent, flat=True)
    entity_alias = aliased(Entity, flat=True)
    created_by_alias = aliased(Person, flat=True)
    updated_by_alias = aliased(Person, flat=True)

    aliases = {
        Agent: {
            "agent": agent_alias,
        },
        Person: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
        Entity: entity_alias,
    }
    facet_keys = []
    filter_keys = [
        "agent",
        "created_by",
        "updated_by",
        "entity",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=Contribution,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    if check_authorized_project:
        filter_query = lambda q: constrain_to_readable_entities(_load(q), user_context.project_id)
    else:
        filter_query = _load

    return app.queries.common.router_read_many(
        db=db,
        db_model_class=Contribution,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=aliases,
        apply_filter_query_operations=filter_query,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=ContributionRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=filter_model,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
        check_authorized_project=check_authorized_project,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ContributionFilterDep,
) -> ListResponse[ContributionRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        check_authorized_project=True,
    )


def admin_read_many(
    user_context: AdminContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ContributionFilterDep,
) -> ListResponse[ContributionRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        check_authorized_project=False,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ContributionRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=Contribution,
        user_context=None,
        response_schema_class=ContributionRead,
        apply_operations=lambda q: constrain_to_readable_entities(
            _load(q), user_context.project_id
        ),
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> ContributionRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=Contribution,
        user_context=None,
        response_schema_class=ContributionRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    contribution: ContributionCreate,
) -> ContributionRead:
    stmt = constrain_entity_query_to_project(
        sa.select(sa.func.count(Entity.id)).where(Entity.id == contribution.entity_id),
        user_context.project_id,
    )
    if db.execute(stmt).scalar_one() == 0:
        L.warning("Attempting to create an annotation for an entity inaccessible to user")
        raise HTTPException(
            status_code=404, detail=f"cannot access entity {contribution.entity_id}"
        )

    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Contribution,
        json_model=contribution,
        response_schema_class=ContributionRead,
        user_context=user_context,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: ContributionUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> ContributionRead:
    def apply_operations(q):
        entity_alias = aliased(Entity)
        q = q.join(entity_alias, entity_alias.id == Contribution.entity_id)
        q = constrain_to_writable_entities(q, user_context, db_model_class=entity_alias)
        return _load(q)

    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=Contribution,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=ContributionRead,
        apply_operations=apply_operations,
        check_authorized_project=False,  # checked with apply_operations
    )


def admin_update_one(
    user_context: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: ContributionAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
):
    return app.queries.common.router_update_one(
        id_=id_,
        db=db,
        db_model_class=Contribution,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=ContributionRead,
        apply_operations=_load,
        check_authorized_project=False,
    )


def delete_one(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    # Fetch contribution with joined entity
    query = _load(sa.select(Contribution).where(Contribution.id == id_))

    with ensure_result(error_message="Contribution not found"):
        contribution = db.execute(query).unique().scalar_one()

    # use entity's authorized_project_id for authorization
    if not is_user_authorized_for_deletion(db, user_context, contribution.entity):
        raise ApiError(
            message="User is not authorized to access resource.",
            error_code=ApiErrorCode.ENTITY_FORBIDDEN,
            http_status_code=HTTPStatus.FORBIDDEN,
        )

    crud.delete_one(db=db, row=contribution)

    return DeleteResponse(id=id_)
