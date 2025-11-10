import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    Circuit,
    Entity,
    Simulation,
    SimulationCampaign,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.simulation_campaign import SimulationCampaignFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.routers import DeleteResponse
from app.schemas.simulation_campaign import (
    SimulationCampaignAdminUpdate,
    SimulationCampaignCreate,
    SimulationCampaignRead,
    SimulationCampaignUserUpdate,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(SimulationCampaign.created_by),
        joinedload(SimulationCampaign.updated_by),
        selectinload(SimulationCampaign.assets),
        selectinload(SimulationCampaign.contributions),
        selectinload(SimulationCampaign.simulations),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SimulationCampaignRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=SimulationCampaign,
        user_context=user_context,
        response_schema_class=SimulationCampaignRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> SimulationCampaignRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=SimulationCampaign,
        user_context=None,
        response_schema_class=SimulationCampaignRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: SimulationCampaignCreate,
    user_context: UserContextWithProjectIdDep,
) -> SimulationCampaignRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=SimulationCampaign,
        response_schema_class=SimulationCampaignRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SimulationCampaignUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> SimulationCampaignRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=SimulationCampaign,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=SimulationCampaignRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SimulationCampaignAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> SimulationCampaignRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=SimulationCampaign,
        user_context=None,
        json_model=json_model,
        response_schema_class=SimulationCampaignRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: SimulationCampaignFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[SimulationCampaignRead]:
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    simulation_alias = aliased(Simulation, flat=True)
    circuit_alias = aliased(Circuit, flat=True)
    entity_alias = aliased(Entity, flat=True)
    aliases: Aliases = {
        Agent: {
            "contribution": agent_alias,
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
        Simulation: simulation_alias,
        Circuit: circuit_alias,
        Entity: entity_alias,
    }
    facet_keys = [
        "created_by",
        "updated_by",
        "contribution",
        "circuit",
        "simulation",
    ]
    filter_keys = [*facet_keys, "entity"]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=SimulationCampaign,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=SimulationCampaign,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=SimulationCampaignRead,
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
        db_model_class=SimulationCampaign,
        user_context=user_context,
    )
