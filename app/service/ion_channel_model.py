import uuid
from typing import TYPE_CHECKING, Annotated

import sqlalchemy as sa
from fastapi import Depends
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import Contribution, Ion, IonChannelModel, Subject
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.errors import ApiError, ApiErrorCode
from app.filters.ion_channel_model import IonChannelModelFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.ion_channel_model import (
    IonChannelModelAdminUpdate,
    IonChannelModelCreate,
    IonChannelModelExpanded,
    IonChannelModelRead,
    IonChannelModelUpdate,
)
from app.schemas.types import ListResponse, Select

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load_minimal(q: Select[IonChannelModel]) -> Select[IonChannelModel]:
    return q.options(
        joinedload(IonChannelModel.subject, innerjoin=True).selectinload(Subject.species),
        joinedload(IonChannelModel.subject, innerjoin=True).selectinload(Subject.strain),
        joinedload(IonChannelModel.brain_region, innerjoin=True),
        raiseload("*"),
    )


def _load_expanded(q: Select[IonChannelModel]) -> Select[IonChannelModel]:
    return _load_minimal(q).options(
        joinedload(IonChannelModel.created_by),
        joinedload(IonChannelModel.updated_by),
        joinedload(IonChannelModel.license),
        selectinload(IonChannelModel.contributions).selectinload(Contribution.agent),
        selectinload(IonChannelModel.contributions).selectinload(Contribution.role),
        selectinload(IonChannelModel.assets),
        raiseload("*"),
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    with_search: SearchDep,
    icm_filter: IonChannelModelFilterDep,
    in_brain_region: InBrainRegionDep,
    facets: FacetsDep,
) -> ListResponse[IonChannelModelRead]:
    subject_alias = aliased(Subject, flat=True)
    aliases: Aliases = {
        Subject: subject_alias,
    }
    facet_keys = [
        "brain_region",
        "subject.species",
        "subject.strain",
    ]
    filter_keys = [
        "brain_region",
        "subject",
        "subject.species",
        "subject.strain",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=IonChannelModel,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        db_model_class=IonChannelModel,
        authorized_project_id=user_context.project_id,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        aliases=aliases,
        apply_data_query_operations=_load_minimal,
        apply_filter_query_operations=None,
        pagination_request=pagination_request,
        response_schema_class=IonChannelModelRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=icm_filter,
        filter_joins=filter_joins,
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> IonChannelModelExpanded:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=IonChannelModel,
        authorized_project_id=user_context.project_id,
        response_schema_class=IonChannelModelExpanded,
        apply_operations=_load_expanded,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
) -> IonChannelModelExpanded:
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=IonChannelModel,
        authorized_project_id=None,
        response_schema_class=IonChannelModelExpanded,
        apply_operations=_load_expanded,
    )


def icm_ion_names_exist(db: SessionDep, ion_channel_model: IonChannelModelCreate):
    """Verifies that all Ion names specified in IonChannelModelCreate exist in the Ion database."""
    ion_names = {ion.ion_name.lower() for ion in ion_channel_model.neuron_block.useion}

    stmt = (
        sa.select(sa.func.count() == len(ion_names)).select_from(Ion).where(Ion.name.in_(ion_names))
    )

    all_names_exist = db.execute(stmt).scalar_one()

    if not all_names_exist:
        msg = "Ion name does not exist"
        raise ApiError(message=msg, error_code=ApiErrorCode.ION_NAME_NOT_FOUND)

    return ion_channel_model


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    ion_channel_model: Annotated[IonChannelModelCreate, Depends(icm_ion_names_exist)],
) -> IonChannelModelRead:
    return router_create_one(
        db=db,
        apply_operations=_load_minimal,
        user_context=user_context,
        json_model=ion_channel_model,
        db_model_class=IonChannelModel,
        response_schema_class=IonChannelModelRead,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: IonChannelModelUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> IonChannelModelRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=IonChannelModel,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=IonChannelModelRead,
        apply_operations=_load_minimal,
    )


def admin_update_one(
    db: SessionDep,
    id_: uuid.UUID,
    json_model: IonChannelModelAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> IonChannelModelRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=IonChannelModel,
        user_context=None,
        json_model=json_model,
        response_schema_class=IonChannelModelRead,
        apply_operations=_load_minimal,
    )
