import uuid

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import Agent, Contribution, MEModel, SingleNeuronSynaptome
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.single_neuron_synaptome import SingleNeuronSynaptomeFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.factory import query_params_factory
from app.schemas.synaptome import SingleNeuronSynaptomeCreate, SingleNeuronSynaptomeRead
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(SingleNeuronSynaptome.me_model).joinedload(MEModel.mtypes),
        joinedload(SingleNeuronSynaptome.me_model).joinedload(MEModel.etypes),
        joinedload(SingleNeuronSynaptome.createdBy),
        joinedload(SingleNeuronSynaptome.updatedBy),
        joinedload(SingleNeuronSynaptome.brain_region),
        joinedload(SingleNeuronSynaptome.createdBy),
        joinedload(SingleNeuronSynaptome.updatedBy),
        selectinload(SingleNeuronSynaptome.contributions).joinedload(Contribution.agent),
        selectinload(SingleNeuronSynaptome.contributions).joinedload(Contribution.role),
        selectinload(SingleNeuronSynaptome.assets),
        raiseload("*"),
    )


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
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: SingleNeuronSynaptomeCreate,
    user_context: UserContextWithProjectIdDep,
) -> SingleNeuronSynaptomeRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=SingleNeuronSynaptome,
        response_schema_class=SingleNeuronSynaptomeRead,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: SingleNeuronSynaptomeFilterDep,
    with_search: SearchDep,
    in_brain_region: InBrainRegionDep,
    facets: FacetsDep,
) -> ListResponse[SingleNeuronSynaptomeRead]:
    me_model_alias = aliased(MEModel, flat=True)
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases = {
        Agent: {
            "contribution": agent_alias,
            "createdBy": created_by_alias,
            "updatedBy": updated_by_alias,
        },
        MEModel: me_model_alias,
    }
    facet_keys = filter_keys = [
        "brain_region",
        "me_model",
        "createdBy",
        "updatedBy",
        "contribution",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=SingleNeuronSynaptome,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=SingleNeuronSynaptome,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=SingleNeuronSynaptomeRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )
