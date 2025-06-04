import uuid
from typing import Annotated

import sqlalchemy as sa
from fastapi import Depends
from sqlalchemy.orm import joinedload, raiseload, selectinload

from app.db.model import Contribution, Ion, IonChannelModel
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
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.factory import query_params_factory
from app.schemas.ion_channel_model import (
    IonChannelModelCreate,
    IonChannelModelExpanded,
    IonChannelModelRead,
)
from app.schemas.types import ListResponse, Select


def _load(q: Select[IonChannelModel]):
    return (
        q.options(joinedload(IonChannelModel.species, innerjoin=True))
        .options(joinedload(IonChannelModel.strain))
        .options(joinedload(IonChannelModel.brain_region))
        .options(raiseload("*"))
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
    facet_keys = filter_keys = [
        "brain_region",
        "species",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=IonChannelModel,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases={},
    )
    return router_read_many(
        db=db,
        db_model_class=IonChannelModel,
        authorized_project_id=user_context.project_id,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        aliases=None,
        apply_data_query_operations=_load,
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
    def _load(q: Select[IonChannelModel]):
        return (
            q.options(joinedload(IonChannelModel.species, innerjoin=True))
            .options(joinedload(IonChannelModel.strain))
            .options(joinedload(IonChannelModel.brain_region))
            .options(joinedload(IonChannelModel.created_by))
            .options(joinedload(IonChannelModel.updated_by))
            .options(selectinload(IonChannelModel.contributions).selectinload(Contribution.agent))
            .options(selectinload(IonChannelModel.contributions).selectinload(Contribution.role))
            .options(selectinload(IonChannelModel.assets))
            .options(raiseload("*"))
        )

    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=IonChannelModel,
        authorized_project_id=user_context.project_id,
        response_schema_class=IonChannelModelExpanded,
        apply_operations=_load,
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
        apply_operations=_load,
        user_context=user_context,
        json_model=ion_channel_model,
        db_model_class=IonChannelModel,
        response_schema_class=IonChannelModelRead,
    )
