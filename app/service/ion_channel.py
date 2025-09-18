import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.model import Agent, IonChannel
from app.dependencies.auth import AdminContextDep
from app.dependencies.common import (
    FacetsDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.ion_channel import IonChannelFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.factory import query_params_factory
from app.schemas.ion_channel import (
    IonChannelCreate,
    IonChannelRead,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(IonChannel.created_by),
        joinedload(IonChannel.updated_by),
        raiseload("*"),
    )


def read_one(
    *,
    db: SessionDep,
    id_: uuid.UUID,
) -> IonChannelRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=IonChannel,
        user_context=None,
        response_schema_class=IonChannelRead,
        apply_operations=_load,
    )


def create_one(
    *,
    db: SessionDep,
    json_model: IonChannelCreate,
    user_context: AdminContextDep,
) -> IonChannelRead:
    return router_create_one(
        db=db,
        db_model_class=IonChannel,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=IonChannelRead,
        apply_operations=_load,
    )


def read_many(
    *,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: IonChannelFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[IonChannelRead]:
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
        db_model_class=IonChannel,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=IonChannel,
        with_search=with_search,
        with_in_brain_region=None,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=IonChannelRead,
        user_context=None,
        filter_joins=filter_joins,
    )
