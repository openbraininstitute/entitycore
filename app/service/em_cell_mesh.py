import uuid
from typing import Annotated

from sqlalchemy.orm import joinedload, raiseload, selectinload

from app.db.model import (
    Contribution,
    EMCellMesh,
    Subject,
)
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
from app.dependencies.filter import FilterDepends
from app.filters.em_cell_mesh import EMCellMeshFilter
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
    router_user_delete_one,
)
from app.queries.factory import query_params_factory
from app.schemas.em_cell_mesh import (
    EMCellMeshCreate,
    EMCellMeshRead,
    EMCellMeshUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse, Select

ExpandDep = Annotated[ExpandPaths, expand_query(EMCellMeshRead, EMCellMesh)]


def _load(q: Select[EMCellMesh]) -> Select[EMCellMesh]:
    """Return the query with the required options to load the data."""
    db_model_class = EMCellMesh
    return q.options(
        joinedload(db_model_class.subject, innerjoin=True).options(
            selectinload(Subject.species), selectinload(Subject.strain)
        ),
        joinedload(db_model_class.brain_region, innerjoin=True),
        joinedload(db_model_class.created_by, innerjoin=True),
        joinedload(db_model_class.updated_by, innerjoin=True),
        joinedload(db_model_class.license),
        joinedload(db_model_class.em_dense_reconstruction_dataset, innerjoin=True),
        joinedload(db_model_class.mtypes),
        selectinload(db_model_class.contributions).options(
            selectinload(Contribution.agent), selectinload(Contribution.role)
        ),
        selectinload(db_model_class.assets),
        raiseload("*"),
    )


def _read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    with_search: SearchDep,
    filter_model: FilterDepends[EMCellMeshFilter],
    in_brain_region: InBrainRegionDep,
    facets: FacetsDep,
    expand: ExpandPaths,
    check_authorized_project: bool,
) -> ListResponse[EMCellMeshRead]:
    facet_keys = [
        "brain_region",
        "subject.species",
        "subject.strain",
        "created_by",
        "updated_by",
        "em_dense_reconstruction_dataset",
        "mtype",
        "release_version",
    ]
    filter_keys = [
        *facet_keys,
        "measurement_annotation.measurement_kind.measurement_item",
        "measurement_annotation.measurement_kind.pref_label",
    ]
    name_to_facet_query_params, join_specs, aliases = query_params_factory(
        db_model_class=EMCellMesh,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
    )
    return router_read_many(
        db=db,
        db_model_class=EMCellMesh,
        authorized_project_id=user_context.project_id,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        aliases=aliases,
        apply_data_query_operations=_load,
        apply_filter_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=EMCellMeshRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=filter_model,
        join_specs=join_specs,
        check_authorized_project=check_authorized_project,
        expand=expand,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: FilterDepends[EMCellMeshFilter],
    with_search: SearchDep,
    with_facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
    expand: ExpandDep = frozenset(),
) -> ListResponse[EMCellMeshRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=with_facets,
        in_brain_region=in_brain_region,
        expand=expand,
        check_authorized_project=True,
    )


def admin_read_many(
    user_context: AdminContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: FilterDepends[EMCellMeshFilter],
    with_search: SearchDep,
    with_facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
    expand: ExpandDep = frozenset(),
) -> ListResponse[EMCellMeshRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=with_facets,
        in_brain_region=in_brain_region,
        expand=expand,
        check_authorized_project=False,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    expand: ExpandDep = frozenset(),
) -> EMCellMeshRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=EMCellMesh,
        user_context=user_context,
        response_schema_class=EMCellMeshRead,
        apply_operations=_load,
        expand=expand,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
    expand: ExpandDep = frozenset(),
) -> EMCellMeshRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=EMCellMesh,
        user_context=None,
        response_schema_class=EMCellMeshRead,
        apply_operations=_load,
        expand=expand,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    json_model: EMCellMeshCreate,
    expand: ExpandDep = frozenset(),
) -> EMCellMeshRead:
    return router_create_one(
        db=db,
        apply_operations=_load,
        user_context=user_context,
        json_model=json_model,
        db_model_class=EMCellMesh,
        response_schema_class=EMCellMeshRead,
        expand=expand,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: EMCellMeshUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
    expand: ExpandDep = frozenset(),
) -> EMCellMeshRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=EMCellMesh,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=EMCellMeshRead,
        apply_operations=_load,
        check_authorized_project=True,
        expand=expand,
    )


def admin_update_one(
    user_context: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: EMCellMeshUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
    expand: ExpandDep = frozenset(),
) -> EMCellMeshRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=EMCellMesh,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=EMCellMeshRead,
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
        db_model_class=EMCellMesh,
        user_context=user_context,
    )
