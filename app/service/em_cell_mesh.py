import uuid
from typing import TYPE_CHECKING

from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import Contribution, EMCellMesh, EMDenseReconstructionDataset, Subject
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.em_cell_mesh import EMCellMeshFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.factory import query_params_factory
from app.schemas.em_cell_mesh import EMCellMeshCreate, EMCellMeshRead
from app.schemas.types import ListResponse, Select

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(q: Select[EMCellMesh]) -> Select[EMCellMesh]:
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
        selectinload(db_model_class.contributions).options(
            selectinload(Contribution.agent), selectinload(Contribution.role)
        ),
        selectinload(db_model_class.assets),
        raiseload("*"),
    )


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
    }
    facet_keys = [
        "brain_region",
        "subject.species",
        "subject.strain",
        "em_dense_reconstruction_dataset",
    ]
    filter_keys = [
        "brain_region",
        "subject",
        "subject.species",
        "subject.strain",
        "em_dense_reconstruction_dataset",
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
) -> EMCellMeshRead:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=EMCellMesh,
        authorized_project_id=user_context.project_id,
        response_schema_class=EMCellMeshRead,
        apply_operations=_load,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    ion_channel_model: EMCellMeshCreate,
) -> EMCellMeshRead:
    return router_create_one(
        db=db,
        apply_operations=_load,
        user_context=user_context,
        json_model=ion_channel_model,
        db_model_class=EMCellMesh,
        response_schema_class=EMCellMeshRead,
    )
