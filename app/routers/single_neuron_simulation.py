import uuid
from typing import Annotated

from fastapi import APIRouter
from fastapi_filter import FilterDepends
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.model import Agent, BrainRegion, Contribution, MEModel, SingleNeuronSimulation
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.single_neuron_simulation import SingleNeuronSimulationFilter
from app.routers.common import (
    FacetQueryParams,
    FacetsDep,
    SearchDep,
    router_create_one,
    router_read_many,
    router_read_one,
)
from app.schemas.simulation import (
    SingleNeuronSimulationCreate,
    SingleNeuronSimulationRead,
)
from app.schemas.types import ListResponse

router = APIRouter(
    prefix="/single-neuron-simulation",
    tags=["single-neuron-simulation"],
)


@router.get("/{id_}")
def read(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SingleNeuronSimulationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=SingleNeuronSimulation,
        authorized_project_id=user_context.project_id,
        response_schema_class=SingleNeuronSimulationRead,
        operations=[
            joinedload(SingleNeuronSimulation.me_model),
            joinedload(SingleNeuronSimulation.brain_region),
        ],
    )


@router.post("")
def create(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    json_model: SingleNeuronSimulationCreate,
) -> SingleNeuronSimulationRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        db_model_class=SingleNeuronSimulation,
        authorized_project_id=user_context.project_id,
        response_schema_class=SingleNeuronSimulationRead,
    )


@router.get("")
def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: Annotated[
        SingleNeuronSimulationFilter, FilterDepends(SingleNeuronSimulationFilter)
    ],
    with_search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[SingleNeuronSimulationRead]:
    agent_alias = aliased(Agent, flat=True)
    me_model_alias = aliased(MEModel, flat=True)
    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "contribution": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
        "brain_region": {"id": BrainRegion.id, "label": BrainRegion.name},
        "me_model": {"id": me_model_alias.id, "label": me_model_alias.name},
    }

    apply_filter_query = lambda query: (
        query.join(BrainRegion, SingleNeuronSimulation.brain_region_id == BrainRegion.id)
        .outerjoin(Contribution, SingleNeuronSimulation.id == Contribution.entity_id)
        .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
        .outerjoin(me_model_alias, SingleNeuronSimulation.me_model_id == me_model_alias.id)
    )
    apply_data_options = lambda query: (
        query.options(joinedload(SingleNeuronSimulation.me_model).joinedload(MEModel.brain_region))
        .options(joinedload(SingleNeuronSimulation.brain_region))
        .options(raiseload("*"))
    )
    return router_read_many(
        db=db,
        user_context=user_context,
        filter_model=filter_model,
        db_model_class=SingleNeuronSimulation,
        with_search=with_search,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=apply_filter_query,
        apply_data_query_operations=apply_data_options,
        aliases={Agent: agent_alias, MEModel: me_model_alias},
        pagination_request=pagination_request,
        response_schema_class=ListResponse[SingleNeuronSimulationRead],
    )
