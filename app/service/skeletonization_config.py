import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    Person,
    SkeletonizationConfig,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.skeletonization_config import SkeletonizationConfigFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
    router_user_delete_one,
)
from app.queries.factory import query_params_factory
from app.schemas.routers import DeleteResponse
from app.schemas.skeletonization_config import (
    SkeletonizationConfigAdminUpdate,
    SkeletonizationConfigCreate,
    SkeletonizationConfigRead,
    SkeletonizationConfigUserUpdate,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases

DBModel = SkeletonizationConfig
ReadSchema = SkeletonizationConfigRead
CreateSchema = SkeletonizationConfigCreate
UserUpdateSchema = SkeletonizationConfigUserUpdate
AdminUpdateSchema = SkeletonizationConfigAdminUpdate
FilterDep = SkeletonizationConfigFilterDep


def _load(query: sa.Select):
    return query.options(
        joinedload(DBModel.created_by),
        joinedload(DBModel.updated_by),
        selectinload(DBModel.assets),
        selectinload(DBModel.contributions),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ReadSchema:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=DBModel,
        user_context=user_context,
        response_schema_class=ReadSchema,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> ReadSchema:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=DBModel,
        user_context=None,
        response_schema_class=ReadSchema,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: CreateSchema,
    user_context: UserContextWithProjectIdDep,
) -> ReadSchema:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=DBModel,
        response_schema_class=ReadSchema,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: UserUpdateSchema,  # pyright: ignore [reportInvalidTypeForm]
) -> ReadSchema:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=DBModel,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=ReadSchema,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: AdminUpdateSchema,  # pyright: ignore [reportInvalidTypeForm]
) -> ReadSchema:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=DBModel,
        user_context=None,
        json_model=json_model,
        response_schema_class=ReadSchema,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: FilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ReadSchema]:
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
        db_model_class=DBModel,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=DBModel,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ReadSchema,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_user_delete_one(
        id_=id_,
        db=db,
        db_model_class=DBModel,
        user_context=user_context,
    )
