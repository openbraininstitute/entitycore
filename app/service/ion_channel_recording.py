import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload, selectinload

from app.db.model import (
    Contribution,
    IonChannelRecording,
    Subject,
)
from app.dependencies.auth import AdminContextDep, UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    ExpandDep,
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.ion_channel_recording import IonChannelRecordingFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
    router_user_delete_one,
)
from app.queries.expand import EntityExpand
from app.queries.factory import query_params_factory
from app.schemas.ion_channel_recording import (
    IonChannelRecordingAdminUpdate,
    IonChannelRecordingCreate,
    IonChannelRecordingRead,
    IonChannelRecordingUserUpdate,
)
from app.schemas.routers import DeleteResponse
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(IonChannelRecording.license),
        joinedload(IonChannelRecording.subject).options(
            joinedload(Subject.species),
            joinedload(Subject.strain),
        ),
        joinedload(IonChannelRecording.brain_region, innerjoin=True),
        joinedload(IonChannelRecording.created_by, innerjoin=True),
        joinedload(IonChannelRecording.updated_by, innerjoin=True),
        selectinload(IonChannelRecording.assets),
        selectinload(IonChannelRecording.stimuli),
        selectinload(IonChannelRecording.contributions).options(
            joinedload(Contribution.agent),
            joinedload(Contribution.role),
        ),
        selectinload(IonChannelRecording.ion_channel),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    expand: ExpandDep = None,
) -> IonChannelRecordingRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=IonChannelRecording,
        user_context=user_context,
        response_schema_class=IonChannelRecordingRead,
        apply_operations=_load,
        expand=expand,
    )


def admin_read_one(
    db: SessionDep,
    id_: uuid.UUID,
    expand: ExpandDep = None,
) -> IonChannelRecordingRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=IonChannelRecording,
        user_context=None,
        response_schema_class=IonChannelRecordingRead,
        apply_operations=_load,
        expand=expand,
    )


def create_one(
    db: SessionDep,
    json_model: IonChannelRecordingCreate,
    user_context: UserContextWithProjectIdDep,
) -> IonChannelRecordingRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=IonChannelRecording,
        response_schema_class=IonChannelRecordingRead,
        apply_operations=_load,
    )


def _read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: IonChannelRecordingFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
    expand: set[EntityExpand] | None,
    check_authorized_project: bool,
) -> ListResponse[IonChannelRecordingRead]:
    facet_keys = [
        "brain_region",
        "created_by",
        "updated_by",
        "contribution",
        "subject.species",
        "subject.strain",
        "ion_channel",
    ]
    filter_keys = [
        *facet_keys,
        "validation_result",
    ]

    name_to_facet_query_params, join_specs, aliases = query_params_factory(
        db_model_class=IonChannelRecording,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=IonChannelRecording,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=IonChannelRecordingRead,
        authorized_project_id=user_context.project_id,
        join_specs=join_specs,
        check_authorized_project=check_authorized_project,
        expand=expand,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: IonChannelRecordingFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
    expand: ExpandDep = None,
) -> ListResponse[IonChannelRecordingRead]:
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
    filter_model: IonChannelRecordingFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
    expand: ExpandDep = None,
) -> ListResponse[IonChannelRecordingRead]:
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
    json_model: IonChannelRecordingUserUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> IonChannelRecordingRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=IonChannelRecording,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=IonChannelRecordingRead,
        apply_operations=_load,
        check_authorized_project=True,
    )


def admin_update_one(
    user_context: AdminContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: IonChannelRecordingAdminUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> IonChannelRecordingRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=IonChannelRecording,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=IonChannelRecordingRead,
        apply_operations=_load,
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
        db_model_class=IonChannelRecording,
        user_context=user_context,
    )
