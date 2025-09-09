import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.model import Agent, ExternalUrl
from app.dependencies.auth import UserContextDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.external_url import ExternalUrlFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.factory import query_params_factory
from app.schemas.external_url import (
    ExternalUrlCreate,
    ExternalUrlRead,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select) -> sa.Select:
    return query.options(
        joinedload(ExternalUrl.created_by, innerjoin=True),
        joinedload(ExternalUrl.updated_by, innerjoin=True),
        raiseload("*"),
    )


def read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> ExternalUrlRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ExternalUrl,
        authorized_project_id=None,
        response_schema_class=ExternalUrlRead,
        apply_operations=_load,
    )


def admin_read_one(db: SessionDep, id_: uuid.UUID) -> ExternalUrlRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ExternalUrl,
        authorized_project_id=None,
        response_schema_class=ExternalUrlRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: ExternalUrlCreate,
    user_context: UserContextDep,  # everybody can create
) -> ExternalUrlRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=ExternalUrl,
        response_schema_class=ExternalUrlRead,
        apply_operations=_load,
    )


def read_many(
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ExternalUrlFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ExternalUrlRead]:
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases: Aliases = {
        Agent: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = [
        "created_by",
        "updated_by",
    ]
    filter_keys = [
        "created_by",
        "updated_by",
    ]

    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=ExternalUrl,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ExternalUrl,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ExternalUrlRead,
        authorized_project_id=None,
        filter_joins=filter_joins,
    )
