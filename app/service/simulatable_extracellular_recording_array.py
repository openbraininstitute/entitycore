import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    Contribution,
    Person,
    SimulatableExtracellularRecordingArray,
)
from app.dependencies.auth import AdminContextDep, UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.simulatable_extracellular_recording_array import (
    SimulatableExtracellularRecordingArrayFilterDep,
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
from app.schemas.simulatable_extracellular_recording_array import (
    SimulatableExtracellularRecordingArrayAdminUpdate,
    SimulatableExtracellularRecordingArrayCreate,
    SimulatableExtracellularRecordingArrayRead,
    SimulatableExtracellularRecordingArrayUserUpdate,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(SimulatableExtracellularRecordingArray.created_by, innerjoin=True),
        joinedload(SimulatableExtracellularRecordingArray.updated_by, innerjoin=True),
        selectinload(SimulatableExtracellularRecordingArray.assets),
        selectinload(SimulatableExtracellularRecordingArray.contributions).options(
            selectinload(Contribution.agent),
            selectinload(Contribution.role),
        ),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SimulatableExtracellularRecordingArrayRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=SimulatableExtracellularRecordingArray,
        user_context=user_context,
        response_schema_class=SimulatableExtracellularRecordingArrayRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> SimulatableExtracellularRecordingArrayRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=SimulatableExtracellularRecordingArray,
        user_context=None,
        response_schema_class=SimulatableExtracellularRecordingArrayRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: SimulatableExtracellularRecordingArrayCreate,
    user_context: UserContextWithProjectIdDep,
) -> SimulatableExtracellularRecordingArrayRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=SimulatableExtracellularRecordingArray,
        response_schema_class=SimulatableExtracellularRecordingArrayRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SimulatableExtracellularRecordingArrayUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> SimulatableExtracellularRecordingArrayRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=SimulatableExtracellularRecordingArray,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=SimulatableExtracellularRecordingArrayRead,
        apply_operations=_load,
        check_authorized_project=True,
    )


def admin_update_one(
    user_context: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: SimulatableExtracellularRecordingArrayAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> SimulatableExtracellularRecordingArrayRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=SimulatableExtracellularRecordingArray,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=SimulatableExtracellularRecordingArrayRead,
        apply_operations=_load,
        check_authorized_project=False,
    )


def _read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: SimulatableExtracellularRecordingArrayFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    check_authorized_project: bool,
) -> ListResponse[SimulatableExtracellularRecordingArrayRead]:
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Person, flat=True)
    updated_by_alias = aliased(Person, flat=True)

    aliases: Aliases = {
        Agent: {
            "contribution": agent_alias,
        },
        Person: {
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
    }
    facet_keys = filter_keys = [
        "created_by",
        "updated_by",
        "contribution",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=SimulatableExtracellularRecordingArray,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=SimulatableExtracellularRecordingArray,
        with_search=with_search,
        with_in_brain_region=None,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=SimulatableExtracellularRecordingArrayRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
        check_authorized_project=check_authorized_project,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: SimulatableExtracellularRecordingArrayFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[SimulatableExtracellularRecordingArrayRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=facets,
        check_authorized_project=True,
    )


def admin_read_many(
    user_context: AdminContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: SimulatableExtracellularRecordingArrayFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[SimulatableExtracellularRecordingArrayRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=facets,
        check_authorized_project=False,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_user_delete_one(
        id_=id_,
        db=db,
        db_model_class=SimulatableExtracellularRecordingArray,
        user_context=user_context,
    )
