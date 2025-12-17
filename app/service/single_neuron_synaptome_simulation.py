import uuid

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    Person,
    SingleNeuronSynaptome,
    SingleNeuronSynaptomeSimulation,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.single_neuron_synaptome_simulation import (
    SingleNeuronSynaptomeSimulationFilterDep,
)
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
    router_user_delete_one,
)
from app.queries.factory import query_params_factory
from app.schemas.routers import DeleteResponse
from app.schemas.simulation import (
    SingleNeuronSynaptomeSimulationAdminUpdate,
    SingleNeuronSynaptomeSimulationCreate,
    SingleNeuronSynaptomeSimulationRead,
    SingleNeuronSynaptomeSimulationUserUpdate,
)
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(SingleNeuronSynaptomeSimulation.synaptome).joinedload(
            SingleNeuronSynaptome.me_model
        ),
        joinedload(SingleNeuronSynaptomeSimulation.synaptome).joinedload(
            SingleNeuronSynaptome.me_model
        ),
        joinedload(SingleNeuronSynaptomeSimulation.brain_region),
        selectinload(SingleNeuronSynaptomeSimulation.assets),
        joinedload(SingleNeuronSynaptomeSimulation.created_by),
        joinedload(SingleNeuronSynaptomeSimulation.updated_by),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SingleNeuronSynaptomeSimulationRead:
    return router_read_one(
        db=db,
        id_=id_,
        user_context=user_context,
        db_model_class=SingleNeuronSynaptomeSimulation,
        response_schema_class=SingleNeuronSynaptomeSimulationRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> SingleNeuronSynaptomeSimulationRead:
    return router_read_one(
        db=db,
        id_=id_,
        user_context=None,
        db_model_class=SingleNeuronSynaptomeSimulation,
        response_schema_class=SingleNeuronSynaptomeSimulationRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: SingleNeuronSynaptomeSimulationCreate,
    db: SessionDep,
) -> SingleNeuronSynaptomeSimulationRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=SingleNeuronSynaptomeSimulation,
        response_schema_class=SingleNeuronSynaptomeSimulationRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SingleNeuronSynaptomeSimulationUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> SingleNeuronSynaptomeSimulationRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=SingleNeuronSynaptomeSimulation,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=SingleNeuronSynaptomeSimulationRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SingleNeuronSynaptomeSimulationAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> SingleNeuronSynaptomeSimulationRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=SingleNeuronSynaptomeSimulation,
        user_context=None,
        json_model=json_model,
        response_schema_class=SingleNeuronSynaptomeSimulationRead,
        apply_operations=_load,
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
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Person, flat=True)
    updated_by_alias = aliased(Person, flat=True)
    aliases = {
        SingleNeuronSynaptome: synaptome_alias,
        Agent: {
            "contribution": agent_alias,
        },
        Person: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = filter_keys = [
        "brain_region",
        "synaptome",
        "created_by",
        "updated_by",
        "contribution",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=SingleNeuronSynaptomeSimulation,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=SingleNeuronSynaptomeSimulation,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=SingleNeuronSynaptomeSimulationRead,
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
        db_model_class=SingleNeuronSynaptomeSimulation,
        user_context=user_context,
    )
