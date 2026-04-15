import uuid
from typing import TYPE_CHECKING

from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import Contribution, EMDenseReconstructionDataset, Person, Subject
from app.dependencies.auth import AdminContextDep, AdminContextWithProjectIdDep, UserContextDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.em_dense_reconstruction_dataset import EMDenseReconstructionDatasetFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
    router_user_delete_one,
)
from app.queries.factory import query_params_factory
from app.schemas.em_dense_reconstruction_dataset import (
    EMDenseReconstructionDatasetAdminUpdate,
    EMDenseReconstructionDatasetCreate,
    EMDenseReconstructionDatasetRead,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse, Select

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(q: Select[EMDenseReconstructionDataset]) -> Select[EMDenseReconstructionDataset]:
    db_model_class = EMDenseReconstructionDataset
    return q.options(
        joinedload(db_model_class.subject, innerjoin=True).selectinload(Subject.species),
        joinedload(db_model_class.subject, innerjoin=True).selectinload(Subject.strain),
        joinedload(db_model_class.brain_region, innerjoin=True),
        joinedload(db_model_class.created_by),
        joinedload(db_model_class.updated_by),
        joinedload(db_model_class.license),
        selectinload(db_model_class.contributions).selectinload(Contribution.agent),
        selectinload(db_model_class.contributions).selectinload(Contribution.role),
        selectinload(db_model_class.assets),
        raiseload("*"),
    )


def _read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    with_search: SearchDep,
    filter_model: EMDenseReconstructionDatasetFilterDep,
    in_brain_region: InBrainRegionDep,
    facets: FacetsDep,
    check_authorized_project: bool,
) -> ListResponse[EMDenseReconstructionDatasetRead]:
    subject_alias = aliased(Subject, flat=True)
    aliases: Aliases = {
        Subject: subject_alias,
        Person: {
            "created_by": aliased(Person, flat=True),
            "updated_by": aliased(Person, flat=True),
        },
    }
    facet_keys = [
        "brain_region",
        "subject.species",
        "subject.strain",
    ]
    filter_keys = [
        "created_by",
        "updated_by",
        "brain_region",
        "subject",
        "subject.species",
        "subject.strain",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=EMDenseReconstructionDataset,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        db_model_class=EMDenseReconstructionDataset,
        authorized_project_id=user_context.project_id,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        aliases=aliases,
        apply_data_query_operations=_load,
        apply_filter_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=EMDenseReconstructionDatasetRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=filter_model,
        filter_joins=filter_joins,
        check_authorized_project=check_authorized_project,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: EMDenseReconstructionDatasetFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[EMDenseReconstructionDatasetRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=facets,
        in_brain_region=in_brain_region,
        check_authorized_project=True,
    )


def admin_read_many(
    user_context: AdminContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: EMDenseReconstructionDatasetFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[EMDenseReconstructionDatasetRead]:
    return _read_many(
        user_context=user_context,
        db=db,
        pagination_request=pagination_request,
        filter_model=filter_model,
        with_search=with_search,
        facets=facets,
        in_brain_region=in_brain_region,
        check_authorized_project=False,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> EMDenseReconstructionDatasetRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=EMDenseReconstructionDataset,
        user_context=user_context,
        response_schema_class=EMDenseReconstructionDatasetRead,
        apply_operations=_load,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> EMDenseReconstructionDatasetRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=EMDenseReconstructionDataset,
        user_context=None,
        response_schema_class=EMDenseReconstructionDatasetRead,
        apply_operations=_load,
    )


def create_one(
    user_context: AdminContextWithProjectIdDep,
    db: SessionDep,
    json_model: EMDenseReconstructionDatasetCreate,
) -> EMDenseReconstructionDatasetRead:
    return router_create_one(
        db=db,
        apply_operations=_load,
        user_context=user_context,
        json_model=json_model,
        db_model_class=EMDenseReconstructionDataset,
        response_schema_class=EMDenseReconstructionDatasetRead,
    )


def update_one(
    user_context: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: EMDenseReconstructionDatasetAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> EMDenseReconstructionDatasetRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=EMDenseReconstructionDataset,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=EMDenseReconstructionDatasetRead,
        apply_operations=_load,
        check_authorized_project=False,
    )


admin_update_one = update_one


def delete_one(
    user_context: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> DeleteResponse:
    return router_user_delete_one(
        id_=id_,
        db=db,
        db_model_class=EMDenseReconstructionDataset,
        user_context=user_context,
    )
