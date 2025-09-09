import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload

import app.queries.common
from app.db.model import Agent, Organization
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.organization import OrganizationFilterDep
from app.queries.factory import query_params_factory
from app.schemas.agent import OrganizationCreate, OrganizationRead
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(Organization.created_by, innerjoin=True),
        joinedload(Organization.updated_by, innerjoin=True),
        raiseload("*"),
    )


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: OrganizationFilterDep,
) -> ListResponse[OrganizationRead]:
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
        db_model_class=Organization,
        filter_keys=filter_keys,
        facet_keys=[],
        aliases=aliases,
    )
    return app.queries.common.router_read_many(
        db=db,
        db_model_class=Organization,
        authorized_project_id=None,
        with_search=None,
        with_in_brain_region=None,
        facets=None,
        aliases=aliases,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        pagination_request=pagination_request,
        response_schema_class=OrganizationRead,
        name_to_facet_query_params=None,
        filter_model=filter_model,
        filter_joins=filter_joins,
    )


def read_one(id_: uuid.UUID, db: SessionDep) -> OrganizationRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=Organization,
        authorized_project_id=None,
        response_schema_class=OrganizationRead,
        apply_operations=_load,
    )


def admin_read_one(db: SessionDep, id_: uuid.UUID) -> OrganizationRead:
    return app.queries.common.router_read_one(
        id_=id_,
        db=db,
        db_model_class=Organization,
        authorized_project_id=None,
        response_schema_class=OrganizationRead,
        apply_operations=_load,
    )


def create_one(
    organization: OrganizationCreate, db: SessionDep, user_context: AdminContextDep
) -> OrganizationRead:
    return app.queries.common.router_create_one(
        db=db,
        db_model_class=Organization,
        json_model=organization,
        response_schema_class=OrganizationRead,
        user_context=user_context,
        apply_operations=_load,
    )
