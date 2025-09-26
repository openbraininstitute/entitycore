import uuid

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import Agent, MEModel, SingleNeuronSimulation
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.single_neuron_simulation import SingleNeuronSimulationFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.simulation import (
    SingleNeuronSimulationAdminUpdate,
    SingleNeuronSimulationCreate,
    SingleNeuronSimulationRead,
    SingleNeuronSimulationUserUpdate,
)
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(SingleNeuronSimulation.me_model).joinedload(MEModel.mtypes),
        joinedload(SingleNeuronSimulation.me_model).joinedload(MEModel.etypes),
        joinedload(SingleNeuronSimulation.brain_region),
        joinedload(SingleNeuronSimulation.created_by),
        joinedload(SingleNeuronSimulation.updated_by),
        selectinload(SingleNeuronSimulation.assets),
        raiseload("*"),
    )


def read_one(
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
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> SingleNeuronSimulationRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=SingleNeuronSimulation,
        authorized_project_id=None,
        response_schema_class=SingleNeuronSimulationRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    json_model: SingleNeuronSimulationCreate,
) -> SingleNeuronSimulationRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=SingleNeuronSimulation,
        response_schema_class=SingleNeuronSimulationRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SingleNeuronSimulationUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> SingleNeuronSimulationRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=SingleNeuronSimulation,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=SingleNeuronSimulationRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SingleNeuronSimulationAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> SingleNeuronSimulationRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=SingleNeuronSimulation,
        user_context=None,
        json_model=json_model,
        response_schema_class=SingleNeuronSimulationRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: SingleNeuronSimulationFilterDep,
    with_search: SearchDep,
    in_brain_region: InBrainRegionDep,
    facets: FacetsDep,
) -> ListResponse[SingleNeuronSimulationRead]:
    me_model_alias = aliased(MEModel, flat=True)
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases = {
        MEModel: me_model_alias,
        Agent: {
            "contribution": agent_alias,
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = filter_keys = [
        "brain_region",
        "me_model",
        "created_by",
        "updated_by",
        "contribution",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=SingleNeuronSimulation,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=SingleNeuronSimulation,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=SingleNeuronSimulationRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> dict:
    return router_delete_one(
        id_=id_,
        db=db,
        db_model_class=SingleNeuronSimulation,
        user_context=user_context,
    )
