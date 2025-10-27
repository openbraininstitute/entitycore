import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.model import Agent, Entity, SimulationGeneration
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.simulation_generation import SimulationGenerationFilterDep
from app.queries.common import (
    router_create_activity_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_activity_one,
)
from app.queries.factory import query_params_factory
from app.schemas.routers import DeleteResponse
from app.schemas.simulation_generation import (
    SimulationGenerationAdminUpdate,
    SimulationGenerationCreate,
    SimulationGenerationRead,
    SimulationGenerationUserUpdate,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(SimulationGeneration.used),
        joinedload(SimulationGeneration.generated),
        joinedload(SimulationGeneration.created_by),
        joinedload(SimulationGeneration.updated_by),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SimulationGenerationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=SimulationGeneration,
        user_context=user_context,
        response_schema_class=SimulationGenerationRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> SimulationGenerationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=SimulationGeneration,
        user_context=None,
        response_schema_class=SimulationGenerationRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: SimulationGenerationCreate,
    user_context: UserContextWithProjectIdDep,
) -> SimulationGenerationRead:
    return router_create_activity_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=SimulationGeneration,
        response_schema_class=SimulationGenerationRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: SimulationGenerationFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[SimulationGenerationRead]:
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
        db_model_class=SimulationGeneration,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=SimulationGeneration,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=SimulationGenerationRead,
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
        db_model_class=SimulationGeneration,
        user_context=user_context,
    )


def update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SimulationGenerationUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
    user_context: UserContextWithProjectIdDep,
) -> SimulationGenerationRead:
    return router_update_activity_one(
        db=db,
        id_=id_,
        json_model=json_model,
        user_context=user_context,
        db_model_class=SimulationGeneration,
        response_schema_class=SimulationGenerationRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SimulationGenerationAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> SimulationGenerationRead:
    return router_update_activity_one(
        db=db,
        id_=id_,
        json_model=json_model,
        user_context=None,
        db_model_class=SimulationGeneration,
        response_schema_class=SimulationGenerationRead,
        apply_operations=_load,
    )
