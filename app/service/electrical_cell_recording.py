import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    Contribution,
    ElectricalCellRecording,
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
from app.filters.electrical_cell_recording import ElectricalCellRecordingFilterDep
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
    router_update_one,
)
from app.queries.factory import query_params_factory
from app.schemas.electrical_cell_recording import (
    ElectricalCellRecordingCreate,
    ElectricalCellRecordingRead,
    ElectricalCellRecordingUpdate,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load(query: sa.Select):
    return query.options(
        joinedload(ElectricalCellRecording.license),
        joinedload(ElectricalCellRecording.subject).joinedload(Subject.species),
        joinedload(ElectricalCellRecording.subject).joinedload(Subject.strain),
        joinedload(ElectricalCellRecording.brain_region),
        joinedload(ElectricalCellRecording.created_by),
        joinedload(ElectricalCellRecording.updated_by),
        selectinload(ElectricalCellRecording.assets),
        selectinload(ElectricalCellRecording.stimuli),
        selectinload(ElectricalCellRecording.contributions).joinedload(Contribution.agent),
        selectinload(ElectricalCellRecording.contributions).joinedload(Contribution.role),
        joinedload(ElectricalCellRecording.etypes),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> ElectricalCellRecordingRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=ElectricalCellRecording,
        authorized_project_id=user_context.project_id,
        response_schema_class=ElectricalCellRecordingRead,
        apply_operations=_load,
    )


def create_one(
    db: SessionDep,
    json_model: ElectricalCellRecordingCreate,
    user_context: UserContextWithProjectIdDep,
) -> ElectricalCellRecordingRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=ElectricalCellRecording,
        response_schema_class=ElectricalCellRecordingRead,
        apply_operations=_load,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: ElectricalCellRecordingFilterDep,
    with_search: SearchDep,
    facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ElectricalCellRecordingRead]:
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    subject_alias = aliased(Subject, flat=True)
    aliases: Aliases = {
        Agent: {
            "contribution": agent_alias,
            "created_by": created_by_alias,
            "updated_by": updated_by_alias,
        },
        Subject: subject_alias,
    }
    facet_keys = [
        "brain_region",
        "created_by",
        "updated_by",
        "contribution",
        "etype",
        "subject.species",
        "subject.strain",
    ]
    filter_keys = [
        "brain_region",
        "created_by",
        "updated_by",
        "contribution",
        "etype",
        "subject",
        "subject.species",
        "subject.strain",
    ]

    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=ElectricalCellRecording,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ElectricalCellRecording,
        with_search=with_search,
        with_in_brain_region=in_brain_region,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load,
        aliases=aliases,
        pagination_request=pagination_request,
        response_schema_class=ElectricalCellRecordingRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )


def update_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    json_model: ElectricalCellRecordingUpdate,  # pyright: ignore [reportInvalidTypeForm]
) -> ElectricalCellRecordingRead:
    return router_update_one(
        id_=id_,
        db=db,
        db_model_class=ElectricalCellRecording,
        user_context=user_context,
        json_model=json_model,
        response_schema_class=ElectricalCellRecordingRead,
        apply_operations=_load,
    )
