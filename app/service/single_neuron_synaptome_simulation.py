import uuid

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
from app.dependencies.common import (
    FacetQueryParams,
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.single_neuron_synaptome_simulation import (
    SingleNeuronSynaptomeSimulationFilterDep,
)
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.simulation import (
    SingleNeuronSynaptomeSimulationCreate,
    SingleNeuronSynaptomeSimulationRead,
)
from app.schemas.types import ListResponse


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


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: SingleNeuronSynaptomeSimulationFilterDep,
    with_search: SearchDep,
    in_brain_region: InBrainRegionDep,
    facets: FacetsDep,
) -> ListResponse[SingleNeuronSynaptomeSimulationRead]:
    synaptome_alias = aliased(SingleNeuronSynaptome, flat=True)
    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "contribution": {
            "id": Agent.id,
            "label": Agent.pref_label,
            "type": Agent.type,
        },
        "brain_region": {"id": BrainRegion.id, "label": BrainRegion.name},
        "single_neuron_synaptome": {"id": synaptome_alias.id, "label": synaptome_alias.name},
    }
    apply_filter_query = lambda query: (
        query.join(BrainRegion, SingleNeuronSynaptomeSimulation.brain_region_id == BrainRegion.id)
        .outerjoin(Contribution, SingleNeuronSynaptomeSimulation.id == Contribution.entity_id)
        .outerjoin(Agent, Contribution.agent_id == Agent.id)
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
        filter_model=filter_model,
        db_model_class=SingleNeuronSynaptomeSimulation,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=apply_filter_query,
        apply_data_query_operations=apply_data_query,
        aliases={SingleNeuronSynaptome: synaptome_alias},
        pagination_request=pagination_request,
        response_schema_class=SingleNeuronSynaptomeSimulationRead,
        authorized_project_id=user_context.project_id,
    )
