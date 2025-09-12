import uuid

import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.orm import aliased, joinedload, raiseload

import app.queries.common
from app.db.auth import constrain_entity_query_to_project, constrain_to_accessible_entities
from app.db.model import Agent, Contribution, Entity
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.common import ContributionFilterDep
from app.logger import L
from app.queries.factory import query_params_factory
from app.schemas.contribution import ContributionCreate, ContributionRead
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


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    filter_model: ContributionFilterDep,
    pagination_request: PaginationQuery,
) -> ListResponse[ContributionRead]:
    agent_alias = aliased(Agent, flat=True)
    entity_alias = aliased(Entity, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)

    aliases = {
        Agent: {
            "agent": agent_alias,
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

    filter_query = lambda q: constrain_to_accessible_entities(_load(q), user_context.project_id)

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
        authorized_project_id=None,
        response_schema_class=ContributionRead,
        apply_operations=lambda q: constrain_to_accessible_entities(
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
        authorized_project_id=None,
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
            status_code=404, detail=f"Cannot access entity {contribution.entity_id}"
        )

    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Contribution,
        json_model=contribution,
        response_schema_class=ContributionRead,
        user_context=user_context,
        apply_operations=_load,
    )
