import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload, selectinload

from app.db.model import (
    AnalysisNotebookEnvironment,
    Contribution,
)
from app.dependencies.auth import AdminContextDep, UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import ExpandDep, FacetsDep, PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.filters.analysis_notebook_environment import AnalysisNotebookEnvironmentFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
    router_user_delete_one,
)
from app.queries.expand import EntityExpand
from app.queries.factory import query_params_factory
from app.schemas.analysis_notebook_environment import (
    AnalysisNotebookEnvironmentAdminUpdate,
    AnalysisNotebookEnvironmentCreate,
    AnalysisNotebookEnvironmentRead,
    AnalysisNotebookEnvironmentUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(AnalysisNotebookEnvironment.created_by),
        joinedload(AnalysisNotebookEnvironment.updated_by),
        selectinload(AnalysisNotebookEnvironment.assets),
        selectinload(AnalysisNotebookEnvironment.contributions).options(
            selectinload(Contribution.agent),
            selectinload(Contribution.role),
        ),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    expand: ExpandDep = None,
) -> AnalysisNotebookEnvironmentRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=AnalysisNotebookEnvironment,
        user_context=user_context,
        response_schema_class=AnalysisNotebookEnvironmentRead,
        apply_operations=_load,
        expand=expand,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
    expand: ExpandDep = None,
) -> AnalysisNotebookEnvironmentRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=AnalysisNotebookEnvironment,
        user_context=None,
        response_schema_class=AnalysisNotebookEnvironmentRead,
        apply_operations=_load,
        expand=expand,
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
    expand: set[EntityExpand] | None,
    check_authorized_project: bool,
) -> ListResponse[AnalysisNotebookEnvironmentRead]:

    facet_keys = filter_keys = [
        "created_by",
        "updated_by",
        "contribution",
    ]
    name_to_facet_query_params, join_specs, aliases = query_params_factory(
        db_model_class=AnalysisNotebookEnvironment,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
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
        join_specs=join_specs,
        check_authorized_project=check_authorized_project,
        expand=expand,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: AnalysisNotebookEnvironmentFilterDep,
    with_search: SearchDep,
    with_facets: FacetsDep,
    expand: ExpandDep = None,
) -> ListResponse[AnalysisNotebookEnvironmentRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=with_facets,
        expand=expand,
        check_authorized_project=True,
    )


def admin_read_many(
    user_context: AdminContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: AnalysisNotebookEnvironmentFilterDep,
    with_search: SearchDep,
    with_facets: FacetsDep,
    expand: ExpandDep = None,
) -> ListResponse[AnalysisNotebookEnvironmentRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=with_facets,
        expand=expand,
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
