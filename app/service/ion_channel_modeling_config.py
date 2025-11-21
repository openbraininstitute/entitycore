import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    IonChannelModelingConfig,
    Person,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.ion_channel_modeling_config import IonChannelModelingConfigFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.ion_channel_modeling_config import (
    IonChannelModelingConfigAdminUpdate,
    IonChannelModelingConfigCreate,
    IonChannelModelingConfigRead,
    IonChannelModelingConfigUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(IonChannelModelingConfig.created_by),
        joinedload(IonChannelModelingConfig.updated_by),
        selectinload(IonChannelModelingConfig.assets),
        selectinload(IonChannelModelingConfig.contributions),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> IonChannelModelingConfigRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=IonChannelModelingConfig,
        user_context=user_context,
        response_schema_class=IonChannelModelingConfigRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> IonChannelModelingConfigRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=IonChannelModelingConfig,
        user_context=None,
        response_schema_class=IonChannelModelingConfigRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: IonChannelModelingConfigCreate,
    user_context: UserContextWithProjectIdDep,
) -> IonChannelModelingConfigRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=IonChannelModelingConfig,
        response_schema_class=IonChannelModelingConfigRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: IonChannelModelingConfigUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> IonChannelModelingConfigRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=IonChannelModelingConfig,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=IonChannelModelingConfigRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: IonChannelModelingConfigAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> IonChannelModelingConfigRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=IonChannelModelingConfig,
        user_context=None,
        json_model=json_model,
        response_schema_class=IonChannelModelingConfigRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: IonChannelModelingConfigFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[IonChannelModelingConfigRead]:
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Person, flat=True)
    updated_by_alias = aliased(Person, flat=True)

    aliases: Aliases = {
        Agent: {
            "contribution": agent_alias,
        },
        Person: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = filter_keys = [
        "created_by",
        "updated_by",
        "contribution",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=IonChannelModelingConfig,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=IonChannelModelingConfig,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=IonChannelModelingConfigRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_delete_one(
        id_=id_,
        db=db,
        db_model_class=IonChannelModelingConfig,
        user_context=user_context,
    )
