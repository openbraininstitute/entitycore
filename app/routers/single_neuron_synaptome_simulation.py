import uuid
from typing import Annotated

from fastapi import APIRouter
from fastapi_filter import FilterDepends
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.model import (
    Agent,
    BrainRegion,
    Contribution,
    MEModel,
    SingleNeuronSynaptome,
    SingleNeuronSynaptomeSimulation,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.single_neuron_synaptome_simulation import SingleNeuronSynaptomeSimulationFilter
from app.routers.common import (
    FacetQueryParams,
    FacetsDep,
    SearchDep,
    router_create_one,
    router_read_many,
    router_read_one,
)
from app.schemas.simulation import (
    SingleNeuronSynaptomeSimulationCreate,
    SingleNeuronSynaptomeSimulationRead,
)
from app.schemas.types import ListResponse

router = APIRouter(
    prefix="/single-neuron-synaptome-simulation",
    tags=["single-neuron-synaptome-simulation"],
)


@router.get("/{id_}")
def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SingleNeuronSynaptomeSimulationRead:
    return router_read_one(
        db=db,
        id_=id_,
        authorized_project_id=user_context.project_id,
        db_model_class=SingleNeuronSynaptomeSimulation,
        response_schema_class=SingleNeuronSynaptomeSimulationRead,
        apply_operations=lambda q: q.options(
            joinedload(SingleNeuronSynaptomeSimulation.synaptome),
            joinedload(SingleNeuronSynaptomeSimulation.brain_region),
        ),
    )


@router.post("")
def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: SingleNeuronSynaptomeSimulationCreate,
    db: SessionDep,
) -> SingleNeuronSynaptomeSimulationRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        db_model_class=SingleNeuronSynaptomeSimulation,
        authorized_project_id=user_context.project_id,
        response_schema_class=SingleNeuronSynaptomeSimulationRead,
    )


@router.get("")
def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: Annotated[
        SingleNeuronSynaptomeSimulationFilter, FilterDepends(SingleNeuronSynaptomeSimulationFilter)
    ],
    with_search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[SingleNeuronSynaptomeSimulationRead]:
    agent_alias = aliased(Agent, flat=True)
    synaptome_alias = aliased(SingleNeuronSynaptome, flat=True)
    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "contribution": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
        "brain_region": {"id": BrainRegion.id, "label": BrainRegion.name},
        "single_neuron_synaptome": {"id": synaptome_alias.id, "label": synaptome_alias.name},
    }
    apply_filter_query = lambda query: (
        query.join(BrainRegion, SingleNeuronSynaptomeSimulation.brain_region_id == BrainRegion.id)
        .outerjoin(Contribution, SingleNeuronSynaptomeSimulation.id == Contribution.entity_id)
        .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
        .outerjoin(
            synaptome_alias, SingleNeuronSynaptomeSimulation.synaptome_id == synaptome_alias.id
        )
    )
    apply_data_query = lambda query: (
        query.options(
            joinedload(SingleNeuronSynaptomeSimulation.synaptome).joinedload(
                SingleNeuronSynaptome.brain_region
            )
        )
        .options(
            joinedload(SingleNeuronSynaptomeSimulation.synaptome)
            .joinedload(SingleNeuronSynaptome.me_model)
            .joinedload(MEModel.brain_region)
        )
        .options(joinedload(SingleNeuronSynaptomeSimulation.brain_region))
        .options(raiseload("*"))
    )
    return router_read_many(
        db=db,
        user_context=user_context,
        filter_model=filter_model,
        db_model_class=SingleNeuronSynaptomeSimulation,
        with_search=with_search,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=apply_filter_query,
        apply_data_query_operations=apply_data_query,
        aliases={Agent: agent_alias, SingleNeuronSynaptome: synaptome_alias},
        pagination_request=pagination_request,
        response_schema_class=ListResponse[SingleNeuronSynaptomeSimulationRead],
    )
