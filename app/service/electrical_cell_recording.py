import uuid

import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload, raiseload, selectinload

from app.db.model import (
    Agent,
    BrainRegion,
    Contribution,
    ElectricalCellRecording,
    Subject,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetQueryParams,
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.electrical_cell_recording import ElectricalCellRecordingFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.electrical_cell_recording import (
    ElectricalCellRecordingCreate,
    ElectricalCellRecordingRead,
)
from app.schemas.types import ListResponse


def _load(query: sa.Select):
    return query.options(
        joinedload(ElectricalCellRecording.license),
        joinedload(ElectricalCellRecording.subject).joinedload(Subject.species),
        joinedload(ElectricalCellRecording.subject),
        joinedload(ElectricalCellRecording.brain_region),
        joinedload(ElectricalCellRecording.created_by),
        joinedload(ElectricalCellRecording.updated_by),
        selectinload(ElectricalCellRecording.assets),
        selectinload(ElectricalCellRecording.stimuli),
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
    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "contribution": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
        "brain_region": {"id": BrainRegion.id, "label": BrainRegion.name},
        "created_by": {
            "id": created_by_alias.id,
            "label": created_by_alias.pref_label,
            "type": created_by_alias.type,
        },
        "updated_by": {
            "id": updated_by_alias.id,
            "label": updated_by_alias.pref_label,
            "type": updated_by_alias.type,
        },
    }
    filter_joins = {
        "brain_region": lambda q: q.join(
            BrainRegion, ElectricalCellRecording.brain_region_id == BrainRegion.id
        ),
        "contribution": lambda q: q.outerjoin(
            Contribution, ElectricalCellRecording.id == Contribution.entity_id
        ).outerjoin(agent_alias, Contribution.agent_id == agent_alias.id),
        "created_by": lambda q: q.outerjoin(
            created_by_alias, ElectricalCellRecording.created_by_id == created_by_alias.id
        ),
        "updated_by": lambda q: q.outerjoin(
            updated_by_alias, ElectricalCellRecording.updated_by_id == updated_by_alias.id
        ),
    }
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
        aliases={
            Agent: {
                "contribution": agent_alias,
                "created_by": created_by_alias,
                "updated_by": updated_by_alias,
            },
        },
        pagination_request=pagination_request,
        response_schema_class=ElectricalCellRecordingRead,
        authorized_project_id=user_context.project_id,
        filter_joins=filter_joins,
    )
