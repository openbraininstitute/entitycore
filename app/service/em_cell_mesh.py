import uuid
from enum import StrEnum, auto
from functools import partial
from typing import TYPE_CHECKING, Annotated

from fastapi import Query
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Contribution,
    EMCellMesh,
    EMDenseReconstructionDataset,
    MeasurementAnnotation,
    MeasurementKind,
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
from app.filters.em_cell_mesh import EMCellMeshFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
    router_user_delete_one,
)
from app.queries.factory import query_params_factory
from app.schemas.em_cell_mesh import (
    EMCellMeshAnnotationExpandedRead,
    EMCellMeshCreate,
    EMCellMeshRead,
    EMCellMeshUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse, Select

if TYPE_CHECKING:
    from app.filters.base import Aliases


class Expandable(StrEnum):
    measurement_annotation = auto()


def _load(q: Select[EMCellMesh], *, expand: set[Expandable] | None = None) -> Select[EMCellMesh]:
    """Return the query with the required options to load the data."""
    db_model_class = EMCellMesh
    query = q.options(
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
    if expand and Expandable.measurement_annotation in expand:
        query = query.options(
            joinedload(db_model_class.measurement_annotation)
            .selectinload(MeasurementAnnotation.measurement_kinds)
            .options(
                selectinload(MeasurementKind.measurement_items),
                selectinload(MeasurementKind.measurement_label),
            ),
            joinedload(db_model_class.measurement_annotation).contains_eager(
                MeasurementAnnotation.entity
            ),
        )
    return query


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    with_search: SearchDep,
    filter_model: EMCellMeshFilterDep,
    in_brain_region: InBrainRegionDep,
    facets: FacetsDep,
) -> ListResponse[EMCellMeshRead]:
    subject_alias = aliased(Subject, flat=True)
    em_dense_reconstruction_dataset_alias = aliased(EMDenseReconstructionDataset, flat=True)
    aliases: Aliases = {
        Subject: subject_alias,
        EMDenseReconstructionDataset: em_dense_reconstruction_dataset_alias,
        Person: {
            "created_by": aliased(Person, flat=True),
            "updated_by": aliased(Person, flat=True),
        },
    }
    facet_keys = [
        "brain_region",
        "subject.species",
        "subject.strain",
        "created_by",
        "updated_by",
        "em_dense_reconstruction_dataset",
        "mtype",
    ]
    filter_keys = [
        "subject",
        *facet_keys,
        "measurement_annotation",
        "measurement_annotation.measurement_kind",
        "measurement_annotation.measurement_kind.measurement_item",
        "measurement_annotation.measurement_kind.pref_label",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=EMCellMesh,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
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
        filter_joins=filter_joins,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    expand: Annotated[set[Expandable] | None, Query()] = None,
) -> EMCellMeshRead | EMCellMeshAnnotationExpandedRead:
    response_schema_class = EMCellMeshAnnotationExpandedRead if expand else EMCellMeshRead
    apply_operations = partial(_load, expand=expand)
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=EMCellMesh,
        user_context=user_context,
        response_schema_class=response_schema_class,
        apply_operations=apply_operations,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> EMCellMeshRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=EMCellMesh,
        user_context=None,
        response_schema_class=EMCellMeshRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    json_model: EMCellMeshCreate,
) -> EMCellMeshRead:
    return router_create_one(
        db=db,
        apply_operations=_load,
        user_context=user_context,
        json_model=json_model,
        db_model_class=EMCellMesh,
        response_schema_class=EMCellMeshRead,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: EMCellMeshUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> EMCellMeshRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=EMCellMesh,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=EMCellMeshRead,
        apply_operations=_load,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: EMCellMeshUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> EMCellMeshRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=EMCellMesh,
        user_context=None,
        json_model=json_model,
        response_schema_class=EMCellMeshRead,
        apply_operations=_load,
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
