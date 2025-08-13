import uuid

import sqlalchemy as sa
from sqlalchemy.orm import raiseload

from app.db.model import ExternalUrl
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
from app.schemas.external_url import (
    ExternalUrlCreate,
    ExternalUrlRead,
)
from app.schemas.types import ListResponse


def _load(query: sa.Select) -> sa.Select:
    return query.options(
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ExternalUrlRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ExternalUrl,
        authorized_project_id=user_context.project_id,
        response_schema_class=ExternalUrlRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextDep,  # everybody can create
    json_model: ExternalUrlCreate,
    db: SessionDep,
) -> ExternalUrlRead:
    return router_create_one(
        db=db,
        user_context=user_context,
        db_model_class=ExternalUrl,
        json_model=json_model,
        response_schema_class=ExternalUrlRead,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ExternalUrlFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ExternalUrlRead]:
    aliases = {}
    name_to_facet_query_params = {}
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
        authorized_project_id=user_context.project_id,
        filter_joins=None,
    )
