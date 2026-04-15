import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    AnalysisNotebookEnvironment,
    Person,
)
from app.dependencies.auth import AdminContextDep, UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import FacetsDep, PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.filters.analysis_notebook_environment import AnalysisNotebookEnvironmentFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
    router_user_delete_one,
)
from app.queries.factory import query_params_factory
from app.schemas.analysis_notebook_environment import (
    AnalysisNotebookEnvironmentAdminUpdate,
    AnalysisNotebookEnvironmentCreate,
    AnalysisNotebookEnvironmentRead,
    AnalysisNotebookEnvironmentUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(AnalysisNotebookEnvironment.created_by),
        joinedload(AnalysisNotebookEnvironment.updated_by),
        selectinload(AnalysisNotebookEnvironment.assets),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> AnalysisNotebookEnvironmentRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=AnalysisNotebookEnvironment,
        user_context=user_context,
        response_schema_class=AnalysisNotebookEnvironmentRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> AnalysisNotebookEnvironmentRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=AnalysisNotebookEnvironment,
        user_context=None,
        response_schema_class=AnalysisNotebookEnvironmentRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: AnalysisNotebookEnvironmentCreate,
    user_context: UserContextWithProjectIdDep,
) -> AnalysisNotebookEnvironmentRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=AnalysisNotebookEnvironment,
        response_schema_class=AnalysisNotebookEnvironmentRead,
        apply_operations=_load,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: AnalysisNotebookEnvironmentUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> AnalysisNotebookEnvironmentRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=AnalysisNotebookEnvironment,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=AnalysisNotebookEnvironmentRead,
        apply_operations=_load,
        check_authorized_project=True,
    )


def admin_update_one(
    user_context: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: AnalysisNotebookEnvironmentAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> AnalysisNotebookEnvironmentRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=AnalysisNotebookEnvironment,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=AnalysisNotebookEnvironmentRead,
        apply_operations=_load,
        check_authorized_project=False,
    )


def _read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: AnalysisNotebookEnvironmentFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    check_authorized_project: bool,
) -> ListResponse[AnalysisNotebookEnvironmentRead]:
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Person, flat=True)
    updated_by_alias = aliased(Person, flat=True)

    aliases: Aliases = {
        Agent: {
            "contribution": agent_alias,
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
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
        db_model_class=AnalysisNotebookEnvironment,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=AnalysisNotebookEnvironment,
        with_search=with_search,
        with_in_brain_region=None,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=AnalysisNotebookEnvironmentRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
        check_authorized_project=check_authorized_project,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: AnalysisNotebookEnvironmentFilterDep,
    with_search: SearchDep,
    with_facets: FacetsDep,
) -> ListResponse[AnalysisNotebookEnvironmentRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=with_facets,
        check_authorized_project=True,
    )


def admin_read_many(
    user_context: AdminContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: AnalysisNotebookEnvironmentFilterDep,
    with_search: SearchDep,
    with_facets: FacetsDep,
) -> ListResponse[AnalysisNotebookEnvironmentRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=with_facets,
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
        db_model_class=AnalysisNotebookEnvironment,
        user_context=user_context,
    )
