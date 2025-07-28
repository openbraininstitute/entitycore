import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload

from app.db.model import ExternalDataSource, Subject
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.external_data_source import ExternalDataSourceFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.external_data_source import (
    ExternalDataSourceCreate,
    ExternalDataSourceRead,
)
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(Subject.species),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ExternalDataSourceRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ExternalDataSource,
        authorized_project_id=user_context.project_id,
        response_schema_class=ExternalDataSourceRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: ExternalDataSourceCreate,
    db: SessionDep,
) -> ExternalDataSourceRead:
    return router_create_one(
        db=db,
        user_context=user_context,
        db_model_class=ExternalDataSource,
        json_model=json_model,
        response_schema_class=ExternalDataSourceRead,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ExternalDataSourceFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ExternalDataSourceRead]:
    aliases = {}
    name_to_facet_query_params = {}
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ExternalDataSource,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ExternalDataSourceRead,
        authorized_project_id=user_context.project_id,
        filter_joins=None,
    )
