import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    Simulation,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.simulation import SimulationFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.simulation import (
    SimulationCreate,
    SimulationRead,
    SimulationUpdate,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(Simulation.created_by),
        joinedload(Simulation.updated_by),
        selectinload(Simulation.assets),
        selectinload(Simulation.contributions),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SimulationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=Simulation,
        authorized_project_id=user_context.project_id,
        response_schema_class=SimulationRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> SimulationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=Simulation,
        authorized_project_id=None,
        response_schema_class=SimulationRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: SimulationCreate,
    user_context: UserContextWithProjectIdDep,
) -> SimulationRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=Simulation,
        response_schema_class=SimulationRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SimulationUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> SimulationRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=Simulation,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=SimulationRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: SimulationFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[SimulationRead]:
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)

    aliases: Aliases = {
        Agent: {
            "contribution": agent_alias,
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        }
    }
    facet_keys = filter_keys = [
        "created_by",
        "updated_by",
        "contribution",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=Simulation,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=Simulation,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=SimulationRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )
