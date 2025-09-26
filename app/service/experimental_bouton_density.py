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
    ExperimentalBoutonDensity,
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
from app.filters.density import ExperimentalBoutonDensityFilterDep
from app.queries.common import (
    router_create_one,
    router_delete_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.density import (
    ExperimentalBoutonDensityAdminUpdate,
    ExperimentalBoutonDensityCreate,
    ExperimentalBoutonDensityRead,
    ExperimentalBoutonDensityUserUpdate,
)
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(ExperimentalBoutonDensity.brain_region),
        joinedload(ExperimentalBoutonDensity.mtypes),
        joinedload(ExperimentalBoutonDensity.subject).joinedload(Subject.species),
        joinedload(ExperimentalBoutonDensity.subject).joinedload(Subject.strain),
        joinedload(ExperimentalBoutonDensity.assets),
        joinedload(ExperimentalBoutonDensity.license),
        joinedload(ExperimentalBoutonDensity.created_by),
        joinedload(ExperimentalBoutonDensity.updated_by),
        selectinload(ExperimentalBoutonDensity.measurements),
        selectinload(ExperimentalBoutonDensity.contributions).selectinload(Contribution.agent),
        selectinload(ExperimentalBoutonDensity.contributions).selectinload(Contribution.role),
        raiseload("*"),
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ExperimentalBoutonDensityFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ExperimentalBoutonDensityRead]:
    subject = aliased(Subject, flat=True)
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases = {
        Subject: subject,
        Agent: {
            "contribution": agent_alias,
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = [
        "brain_region",
        "created_by",
        "updated_by",
        "contribution",
        "mtype",
        "subject.species",
        "subject.strain",
    ]
    filter_keys = [
        "brain_region",
        "created_by",
        "updated_by",
        "contribution",
        "mtype",
        "subject",
        "subject.species",
        "subject.strain",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=ExperimentalBoutonDensity,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ExperimentalBoutonDensity,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ExperimentalBoutonDensityRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ExperimentalBoutonDensityRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ExperimentalBoutonDensity,
        authorized_project_id=user_context.project_id,
        response_schema_class=ExperimentalBoutonDensityRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> ExperimentalBoutonDensityRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ExperimentalBoutonDensity,
        authorized_project_id=None,
        response_schema_class=ExperimentalBoutonDensityRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    json_model: ExperimentalBoutonDensityCreate,
    db: SessionDep,
) -> ExperimentalBoutonDensityRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=ExperimentalBoutonDensity,
        response_schema_class=ExperimentalBoutonDensityRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: ExperimentalBoutonDensityUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> ExperimentalBoutonDensityRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=ExperimentalBoutonDensity,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=ExperimentalBoutonDensityRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: ExperimentalBoutonDensityAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> ExperimentalBoutonDensityRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=ExperimentalBoutonDensity,
        user_context=None,
        json_model=json_model,
        response_schema_class=ExperimentalBoutonDensityRead,
        apply_operations=_load,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> dict:
    return router_delete_one(
        id_=id_,
        db=db,
        db_model_class=ExperimentalBoutonDensity,
        user_context=user_context,
    )
