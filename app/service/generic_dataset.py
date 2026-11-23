import uuid
from typing import Annotated

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload, selectinload

from app.db.model import (
    Contribution,
    GenericDataset,
    Subject,
)
from app.dependencies.admin_create import AdminCreateDep
from app.dependencies.auth import AdminContextDep, UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    ExpandPaths,
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
    expand_query,
)
from app.dependencies.db import SessionDep
from app.dependencies.filter import FilterDep
from app.filters.generic_dataset import GenericDatasetFilter
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
    router_user_delete_one,
)
from app.queries.factory import query_params_factory
from app.schemas.auth import UserContext, UserContextWithProjectId
from app.schemas.generic_dataset import (
    GenericDatasetAdminCreate,
    GenericDatasetAdminUpdate,
    GenericDatasetCreate,
    GenericDatasetRead,
    GenericDatasetUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse

ExpandDep = Annotated[ExpandPaths, expand_query(GenericDatasetRead, GenericDataset)]


def _load(query: sa.Select):
    return query.options(
        joinedload(GenericDataset.license),
        joinedload(GenericDataset.subject).options(
            joinedload(Subject.species),
            joinedload(Subject.strain),
        ),
        joinedload(GenericDataset.brain_region),
        joinedload(GenericDataset.created_by, innerjoin=True),
        joinedload(GenericDataset.updated_by, innerjoin=True),
        selectinload(GenericDataset.assets),
        selectinload(GenericDataset.contributions).options(
            joinedload(Contribution.agent),
            joinedload(Contribution.role),
        ),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    expand: ExpandDep = frozenset(),
) -> GenericDatasetRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=GenericDataset,
        user_context=user_context,
        response_schema_class=GenericDatasetRead,
        apply_operations=_load,
        expand=expand,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
    expand: ExpandDep = frozenset(),
) -> GenericDatasetRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=GenericDataset,
        user_context=None,
        response_schema_class=GenericDatasetRead,
        apply_operations=_load,
        expand=expand,
    )


def _create_one(
    *,
    db: SessionDep,
    json_model: GenericDatasetCreate,
    user_context: UserContext | UserContextWithProjectId,
    expand: ExpandPaths,
) -> GenericDatasetRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=GenericDataset,
        response_schema_class=GenericDatasetRead,
        apply_operations=_load,
        expand=expand,
    )


def create_one(
    db: SessionDep,
    json_model: GenericDatasetCreate,
    user_context: UserContextWithProjectIdDep,
    expand: ExpandDep = frozenset(),
) -> GenericDatasetRead:
    return _create_one(db=db, json_model=json_model, user_context=user_context, expand=expand)


def admin_create_one(
    db: SessionDep,
    json_model: AdminCreateDep[GenericDatasetAdminCreate],
    user_context: AdminContextDep,
    expand: ExpandDep = frozenset(),
) -> GenericDatasetRead:
    return _create_one(db=db, json_model=json_model, user_context=user_context, expand=expand)


def _read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: FilterDep[GenericDatasetFilter],
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
    expand: ExpandPaths,
    check_authorized_project: bool,
) -> ListResponse[GenericDatasetRead]:
    facet_keys = filter_keys = [
        "created_by",
        "updated_by",
        "brain_region",
        "contribution",
        "subject.species",
        "subject.strain",
    ]

    name_to_facet_query_params, join_specs, aliases = query_params_factory(
        db_model_class=GenericDataset,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=GenericDataset,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=GenericDatasetRead,
        authorized_project_id=user_context.project_id,
        join_specs=join_specs,
        check_authorized_project=check_authorized_project,
        expand=expand,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: FilterDep[GenericDatasetFilter],
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
    expand: ExpandDep = frozenset(),
) -> ListResponse[GenericDatasetRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=facets,
        in_brain_region=in_brain_region,
        expand=expand,
        check_authorized_project=True,
    )


def admin_read_many(
    user_context: AdminContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: FilterDep[GenericDatasetFilter],
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
    expand: ExpandDep = frozenset(),
) -> ListResponse[GenericDatasetRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=facets,
        in_brain_region=in_brain_region,
        expand=expand,
        check_authorized_project=False,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: GenericDatasetUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
    expand: ExpandDep = frozenset(),
) -> GenericDatasetRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=GenericDataset,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=GenericDatasetRead,
        apply_operations=_load,
        check_authorized_project=True,
        expand=expand,
    )


def admin_update_one(
    user_context: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: GenericDatasetAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
    expand: ExpandDep = frozenset(),
) -> GenericDatasetRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=GenericDataset,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=GenericDatasetRead,
        apply_operations=_load,
        check_authorized_project=False,
        expand=expand,
    )


def delete_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_user_delete_one(
        id_=id_,
        db=db,
        db_model_class=GenericDataset,
        user_context=user_context,
    )
