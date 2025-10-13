import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.model import Agent, Entity, IonChannelModelingGeneration
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.ion_channel_modeling_generation import IonChannelModelingGenerationFilterDep
from app.queries.common import (
    router_create_activity_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_activity_one,
)
from app.queries.factory import query_params_factory
from app.schemas.ion_channel_modeling_generation import (
    IonChannelModelingGenerationAdminUpdate,
    IonChannelModelingGenerationCreate,
    IonChannelModelingGenerationRead,
    IonChannelModelingGenerationUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(IonChannelModelingGeneration.used),
        joinedload(IonChannelModelingGeneration.generated),
        joinedload(IonChannelModelingGeneration.created_by),
        joinedload(IonChannelModelingGeneration.updated_by),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> IonChannelModelingGenerationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=IonChannelModelingGeneration,
        authorized_project_id=user_context.project_id,
        response_schema_class=IonChannelModelingGenerationRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> IonChannelModelingGenerationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=IonChannelModelingGeneration,
        authorized_project_id=None,
        response_schema_class=IonChannelModelingGenerationRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: IonChannelModelingGenerationCreate,
    user_context: UserContextWithProjectIdDep,
) -> IonChannelModelingGenerationRead:
    return router_create_activity_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=IonChannelModelingGeneration,
        response_schema_class=IonChannelModelingGenerationRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: IonChannelModelingGenerationFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[IonChannelModelingGenerationRead]:
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    used_alias = aliased(Entity, flat=True)
    generated_alias = aliased(Entity, flat=True)

    aliases: Aliases = {
        Agent: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
        Entity: {
            "used": used_alias,
            "generated": generated_alias,
        },
    }
    facet_keys = []
    filter_keys = ["created_by", "updated_by", "used", "generated"]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=IonChannelModelingGeneration,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=IonChannelModelingGeneration,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=IonChannelModelingGenerationRead,
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
        db_model_class=IonChannelModelingGeneration,
        user_context=user_context,
    )


def update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: IonChannelModelingGenerationUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
    user_context: UserContextWithProjectIdDep,
) -> IonChannelModelingGenerationRead:
    return router_update_activity_one(
        db=db,
        id_=id_,
        json_model=json_model,
        user_context=user_context,
        db_model_class=IonChannelModelingGeneration,
        response_schema_class=IonChannelModelingGenerationRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: IonChannelModelingGenerationAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> IonChannelModelingGenerationRead:
    return router_update_activity_one(
        db=db,
        id_=id_,
        json_model=json_model,
        user_context=None,
        db_model_class=IonChannelModelingGeneration,
        response_schema_class=IonChannelModelingGenerationRead,
        apply_operations=_load,
    )
