import uuid
from typing import Annotated, NotRequired, TypedDict

import sqlalchemy as sa
from fastapi import APIRouter
from fastapi_filter import FilterDepends
from sqlalchemy.orm import InstrumentedAttribute, Session, aliased, joinedload, raiseload

from app.db.auth import constrain_to_accessible_entities
from app.db.model import Agent, Contribution, MEModel, SingleNeuronSimulation
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.single_neuron_simulation import SingleNeuronSimulationFilter
from app.schemas.simulation import (
    SingleNeuronSimulationCreate,
    SingleNeuronSimulationRead,
)
from app.schemas.types import Facet, Facets, ListResponse, PaginationResponse


class FacetQueryParams(TypedDict):
    id: InstrumentedAttribute[uuid.UUID]
    label: InstrumentedAttribute[str]
    type: NotRequired[InstrumentedAttribute[str]]


router = APIRouter(
    prefix="/single-neuron-simulation",
    tags=["single-neuron-simulation"],
)


@router.get("/{id_}")
def read(
    db: SessionDep,
    id_: uuid.UUID,
    project_context: VerifiedProjectContextHeader,
) -> SingleNeuronSimulationRead:
    with ensure_result(error_message="SingleNeuronSimulation not found"):
        query = (
            constrain_to_accessible_entities(
                sa.select(SingleNeuronSimulation),
                project_context.project_id,
            )
            .filter(SingleNeuronSimulation.id == id_)
            .options(joinedload(SingleNeuronSimulation.me_model))
            .options(joinedload(SingleNeuronSimulation.brain_region))
        )

        row = db.execute(query).unique().scalar_one()

    return SingleNeuronSimulationRead.model_validate(row)


@router.post(
    "",
    response_model=SingleNeuronSimulationRead,
)
def create(
    project_context: VerifiedProjectContextHeader,
    json_model: SingleNeuronSimulationCreate,
    db: SessionDep,
):
    kwargs = json_model.model_dump() | {"authorized_project_id": project_context.project_id}

    db_model = SingleNeuronSimulation(**kwargs)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)

    return db_model


def _get_facets(
    db: Session,
    query: sa.Select,
    name_to_facet_query_params: dict[str, FacetQueryParams],
    count_distinct_field: InstrumentedAttribute,
) -> Facets:
    facets = {}
    groupby_keys = ["id", "label", "type"]
    orderby_keys = ["label"]
    for facet_type, fields in name_to_facet_query_params.items():
        groupby_fields = {"type": sa.literal(facet_type), **fields}
        groupby_columns = [groupby_fields[key].label(key) for key in groupby_keys]  # type: ignore[attr-defined]
        groupby_ids = [sa.literal(i + 1) for i in range(len(groupby_columns))]
        facet_q = (
            query.with_only_columns(
                *groupby_columns,
                sa.func.count(sa.func.distinct(count_distinct_field)).label("count"),
            )
            .group_by(*groupby_ids)
            .order_by(*orderby_keys)
        )
        facets[facet_type] = [
            Facet.model_validate(row, from_attributes=True)
            for row in db.execute(facet_q).all()
            if row.id is not None  # exclude null rows if present
        ]

    return facets


@router.get("")
def query(
    db: SessionDep,
    project_context: VerifiedProjectContextHeader,
    pagination_request: PaginationQuery,
    filter_model: Annotated[
        SingleNeuronSimulationFilter, FilterDepends(SingleNeuronSimulationFilter)
    ],
    search: str | None = None,
    with_facets: bool | None = None,  # noqa: FBT001
) -> ListResponse[SingleNeuronSimulationRead]:
    agent_alias = aliased(Agent, flat=True)
    me_model_alias = aliased(MEModel, flat=True)
    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "contribution": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
    }

    filter_query = (
        constrain_to_accessible_entities(
            sa.select(SingleNeuronSimulation),
            project_id=project_context.project_id,
        )
        .outerjoin(Contribution, SingleNeuronSimulation.id == Contribution.entity_id)
        .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
        .outerjoin(me_model_alias, SingleNeuronSimulation.me_model_id == me_model_alias.id)
    )

    if search:
        filter_query = filter_query.where(SingleNeuronSimulation.description_vector.match(search))

    filter_query = filter_model.filter(
        filter_query, aliases={Agent: agent_alias, MEModel: me_model_alias}
    )

    if with_facets:
        facets = _get_facets(
            db,
            filter_query,
            name_to_facet_query_params=name_to_facet_query_params,
            count_distinct_field=SingleNeuronSimulation.id,
        )
    else:
        facets = None

    distinct_ids_subquery = (
        filter_model.sort(filter_query)
        .with_only_columns(SingleNeuronSimulation)
        .distinct()
        .offset(pagination_request.offset)
        .limit(pagination_request.page_size)
    ).subquery("distinct_ids")

    data_query = (
        filter_model.sort(sa.Select(SingleNeuronSimulation))  # sort without filtering
        .join(distinct_ids_subquery, SingleNeuronSimulation.id == distinct_ids_subquery.c.id)
        .options(joinedload(SingleNeuronSimulation.me_model).joinedload(MEModel.brain_region))
        .options(joinedload(SingleNeuronSimulation.brain_region))
        .options(raiseload("*"))
    )

    # unique is needed b/c it contains results that include joined eager loads against collections
    data = db.execute(data_query).scalars().unique()

    total_items = db.execute(
        filter_query.with_only_columns(
            sa.func.count(sa.func.distinct(SingleNeuronSimulation.id)).label("count")
        )
    ).scalar_one()

    response = ListResponse[SingleNeuronSimulationRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=facets,
    )

    return response
