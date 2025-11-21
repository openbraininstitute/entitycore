import uuid

import sqlalchemy as sa
from sqlalchemy.orm import (
    aliased,
    joinedload,
    raiseload,
    selectinload,
)

from app.db.model import (
    Agent,
    Contribution,
    ExperimentalNeuronDensity,
    Person,
    Subject,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.density import ExperimentalNeuronDensityFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.density import (
    ExperimentalNeuronDensityAdminUpdate,
    ExperimentalNeuronDensityCreate,
    ExperimentalNeuronDensityRead,
    ExperimentalNeuronDensityUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(ExperimentalNeuronDensity.brain_region),
        joinedload(ExperimentalNeuronDensity.mtypes),
        joinedload(ExperimentalNeuronDensity.etypes),
        joinedload(ExperimentalNeuronDensity.assets),
        joinedload(ExperimentalNeuronDensity.license),
        joinedload(ExperimentalNeuronDensity.subject).joinedload(Subject.strain),
        joinedload(ExperimentalNeuronDensity.subject).joinedload(Subject.species),
        joinedload(ExperimentalNeuronDensity.created_by),
        joinedload(ExperimentalNeuronDensity.updated_by),
        selectinload(ExperimentalNeuronDensity.measurements),
        selectinload(ExperimentalNeuronDensity.contributions).selectinload(Contribution.agent),
        selectinload(ExperimentalNeuronDensity.contributions).selectinload(Contribution.role),
        raiseload("*"),
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ExperimentalNeuronDensityFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ExperimentalNeuronDensityRead]:
    subject_alias = aliased(Subject, flat=True)
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Person, flat=True)
    updated_by_alias = aliased(Person, flat=True)
    aliases = {
        Subject: subject_alias,
        Agent: {
            "contribution": agent_alias,
        },
        Person: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = [
        "brain_region",
        "created_by",
        "updated_by",
        "contribution",
        "etype",
        "mtype",
        "subject.species",
        "subject.strain",
    ]
    filter_keys = [
        "brain_region",
        "created_by",
        "updated_by",
        "contribution",
        "etype",
        "mtype",
        "subject",
        "subject.species",
        "subject.strain",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=ExperimentalNeuronDensity,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ExperimentalNeuronDensity,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ExperimentalNeuronDensityRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ExperimentalNeuronDensityRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ExperimentalNeuronDensity,
        user_context=user_context,
        response_schema_class=ExperimentalNeuronDensityRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> ExperimentalNeuronDensityRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ExperimentalNeuronDensity,
        user_context=None,
        response_schema_class=ExperimentalNeuronDensityRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: ExperimentalNeuronDensityCreate,
    db: SessionDep,
) -> ExperimentalNeuronDensityRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=ExperimentalNeuronDensity,
        response_schema_class=ExperimentalNeuronDensityRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: ExperimentalNeuronDensityUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> ExperimentalNeuronDensityRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=ExperimentalNeuronDensity,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=ExperimentalNeuronDensityRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: ExperimentalNeuronDensityAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> ExperimentalNeuronDensityRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=ExperimentalNeuronDensity,
        user_context=None,
        json_model=json_model,
        response_schema_class=ExperimentalNeuronDensityRead,
        apply_operations=_load,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_delete_one(
        id_=id_,
        db=db,
        db_model_class=ExperimentalNeuronDensity,
        user_context=user_context,
    )
