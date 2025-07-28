import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload

from app.db.model import IonChannel, Subject
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.ion_channel import IonChannelFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.ion_channel import (
    IonChannelCreate,
    IonChannelRead,
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
) -> IonChannelRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=IonChannel,
        authorized_project_id=user_context.project_id,
        response_schema_class=IonChannelRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model:IonChannelCreate,
    db: SessionDep,
) -> IonChannelRead:
    return router_create_one(
        db=db,
        user_context=user_context,
        db_model_class=IonChannel,
        json_model=json_model,
        response_schema_class=IonChannelRead,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: IonChannelFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[IonChannelRead]:
    aliases = {}
    name_to_facet_query_params = {}
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=IonChannel,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=IonChannelRead,
        authorized_project_id=user_context.project_id,
        filter_joins=None,
    )
