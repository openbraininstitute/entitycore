import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload

import app.queries.common
from app.db.model import Agent, Consortium
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.consortium import ConsortiumFilterDep
from app.queries.factory import query_params_factory
from app.schemas.agent import ConsortiumCreate, ConsortiumRead
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(Consortium.created_by, innerjoin=True),
        joinedload(Consortium.updated_by, innerjoin=True),
        raiseload("*"),
    )


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ConsortiumFilterDep,
) -> ListResponse[ConsortiumRead]:
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases: Aliases = {
        Agent: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        }
    }
    filter_keys = [
        "created_by",
        "updated_by",
    ]
    _, filter_joins = query_params_factory(
        db_model_class=Consortium,
        filter_keys=filter_keys,
        facet_keys=[],
        aliases=aliases,
    )
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=Consortium,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=aliases,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=ConsortiumRead,
        name_to_facet_query_params=None,
        filter_model=filter_model,
        filter_joins=filter_joins,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> ConsortiumRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=Consortium,
        authorized_project_id=None,
        response_schema_class=ConsortiumRead,
        apply_operations=_load,
    )


def admin_read_one(db: SessionDep, id_: uuid.UUID) -> ConsortiumRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=Consortium,
        authorized_project_id=None,
        response_schema_class=ConsortiumRead,
        apply_operations=_load,
    )


def create_one(
    json_model: ConsortiumCreate, db: SessionDep, user_context: AdminContextDep
) -> ConsortiumRead:
    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Consortium,
        json_model=json_model,
        response_schema_class=ConsortiumRead,
        user_context=user_context,
        apply_operations=_load,
    )
