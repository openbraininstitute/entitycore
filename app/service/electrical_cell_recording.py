import uuid
from typing import Annotated

from fastapi_filter import FilterDepends
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    BrainRegion,
    Contribution,
    ElectricalCellRecording,
    ElectricalRecordingStimulus,
    Subject,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import FacetQueryParams, FacetsDep, PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.filters.electrical_cell_recording import ElectricalCellRecordingFilter
from app.queries.common import (
    router_create_one,
    router_read_many,
    router_read_one,
)
from app.schemas.electrical_cell_recording import (
    ElectricalCellRecordingCreate,
    ElectricalCellRecordingRead,
)
from app.schemas.types import ListResponse


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
        apply_operations=lambda q: q.options(
            joinedload(ElectricalCellRecording.license),
            joinedload(ElectricalCellRecording.subject).joinedload(Subject.species),
            joinedload(ElectricalCellRecording.subject).joinedload(Subject.age),
            joinedload(ElectricalCellRecording.brain_region),
            selectinload(ElectricalCellRecording.assets),
            selectinload(ElectricalCellRecording.stimuli),
            raiseload("*"),
        ),
    )


def create_one(
    db: SessionDep,
    json_model: ElectricalCellRecordingCreate,
    user_context: UserContextWithProjectIdDep,
) -> ElectricalCellRecordingRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        db_model_class=ElectricalCellRecording,
        authorized_project_id=user_context.project_id,
        response_schema_class=ElectricalCellRecordingRead,
    )


def read_many(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: Annotated[
        ElectricalCellRecordingFilter, FilterDepends(ElectricalCellRecordingFilter)
    ],
    with_search: SearchDep,
    facets: FacetsDep,
) -> ListResponse[ElectricalCellRecordingRead]:
    agent_alias = aliased(Agent, flat=True)
    protocol_alias = aliased(ElectricalRecordingStimulus, flat=True)
    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "contribution": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
        "brain_region": {"id": BrainRegion.id, "label": BrainRegion.name},
    }
    apply_filter_query = lambda query: (
        query.join(BrainRegion, ElectricalCellRecording.brain_region_id == BrainRegion.id)
        .outerjoin(Contribution, ElectricalCellRecording.id == Contribution.entity_id)
        .outerjoin(
            protocol_alias,
            ElectricalCellRecording.id == protocol_alias.recording_id,
        )
        .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
    )
    apply_data_query = lambda query: (
        query.options(joinedload(ElectricalCellRecording.subject).joinedload(Subject.species))
        .options(joinedload(ElectricalCellRecording.subject).joinedload(Subject.age))
        .options(joinedload(ElectricalCellRecording.brain_region))
        .options(joinedload(ElectricalCellRecording.license))
        .options(selectinload(ElectricalCellRecording.assets))
        .options(selectinload(ElectricalCellRecording.stimuli))
        .options(raiseload("*"))
    )
    return router_read_many(
        db=db,
        filter_model=filter_model,
        db_model_class=ElectricalCellRecording,
        with_search=with_search,
        facets=facets,
        name_to_facet_query_params=name_to_facet_query_params,
        apply_filter_query_operations=apply_filter_query,
        apply_data_query_operations=apply_data_query,
        aliases={Agent: agent_alias, ElectricalRecordingStimulus: protocol_alias},
        pagination_request=pagination_request,
        response_schema_class=ElectricalCellRecordingRead,
        authorized_project_id=user_context.project_id,
    )
