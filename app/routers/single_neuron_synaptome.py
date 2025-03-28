import uuid
from typing import Annotated

from fastapi import APIRouter
from fastapi_filter import FilterDepends
from sqlalchemy.orm import aliased, joinedload, raiseload

from app.db.model import Agent, BrainRegion, Contribution, MEModel, SingleNeuronSynaptome
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.single_neuron_synaptome import SingleNeuronSynaptomeFilter
from app.routers.common import (
    FacetQueryParams,
    FacetsDep,
    SearchDep,
    router_create_one,
    router_read_many,
    router_read_one,
)
from app.schemas.synaptome import (
    SingleNeuronSynaptomeCreate,
    SingleNeuronSynaptomeRead,
)
from app.schemas.types import ListResponse

router = APIRouter(
    prefix="/single-neuron-synaptome",
    tags=["single-neuron-synaptome"],
)


@router.get("/{id_}")
def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SingleNeuronSynaptomeRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=SingleNeuronSynaptome,
        authorized_project_id=user_context.project_id,
        response_schema_class=SingleNeuronSynaptomeRead,
        operations=[
            joinedload(SingleNeuronSynaptome.me_model),
            joinedload(SingleNeuronSynaptome.brain_region),
        ],
    )


@router.post("")
def create_one(
    db: SessionDep,
    json_model: SingleNeuronSynaptomeCreate,
    user_context: UserContextWithProjectIdDep,
) -> SingleNeuronSynaptomeRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        db_model_class=SingleNeuronSynaptome,
        authorized_project_id=user_context.project_id,
        response_schema_class=SingleNeuronSynaptomeRead,
    )


@router.get("")
def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: Annotated[
        SingleNeuronSynaptomeFilter, FilterDepends(SingleNeuronSynaptomeFilter)
    ],
    with_search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[SingleNeuronSynaptomeRead]:
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
        query.join(BrainRegion, SingleNeuronSynaptome.brain_region_id == BrainRegion.id)
        .outerjoin(Contribution, SingleNeuronSynaptome.id == Contribution.entity_id)
        .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
        .outerjoin(me_model_alias, SingleNeuronSynaptome.me_model_id == me_model_alias.id)
    )
    apply_data_query = lambda query: (
        query.options(joinedload(SingleNeuronSynaptome.me_model).joinedload(MEModel.brain_region))
        .options(joinedload(SingleNeuronSynaptome.brain_region))
        .options(raiseload("*"))
    )
    return router_read_many(
        db=db,
        user_context=user_context,
        filter_model=filter_model,
        db_model_class=SingleNeuronSynaptome,
        with_search=with_search,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=apply_filter_query,
        apply_data_query_operations=apply_data_query,
        aliases={Agent: agent_alias, MEModel: me_model_alias},
        pagination_request=pagination_request,
        response_schema_class=ListResponse[SingleNeuronSynaptomeRead],
    )
