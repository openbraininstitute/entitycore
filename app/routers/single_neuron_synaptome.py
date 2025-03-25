import uuid
from typing import Annotated

import sqlalchemy as sa
from fastapi import APIRouter
from fastapi_filter import FilterDepends
from sqlalchemy.orm import InstrumentedAttribute, Session, aliased, joinedload, raiseload

from app.db.auth import constrain_to_accessible_entities
from app.db.model import Agent, BrainRegion, Contribution, MEModel, SingleNeuronSynaptome
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.filters.single_neuron_synaptome import SingleNeuronSynaptomeFilter
from app.routers.common import FacetQueryParams, router_create_one, router_read_one
from app.schemas.synaptome import (
    SingleNeuronSynaptomeCreate,
    SingleNeuronSynaptomeRead,
)
from app.schemas.types import Facet, Facets, ListResponse, PaginationResponse

router = APIRouter(
    prefix="/single-neuron-synaptome",
    tags=["single-neuron-synaptome"],
)


@router.get("/{id_}")
def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> SingleNeuronSynaptomeRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=SingleNeuronSynaptome,
        authorized_project_id=user_context.project_id,
        response_schema_class=SingleNeuronSynaptomeRead,
        operations=[
            joinedload(SingleNeuronSynaptome.me_model),
            joinedload(SingleNeuronSynaptome.brain_region),
        ],
    )


@router.post("")
def create_one(
    db: SessionDep,
    json_model: SingleNeuronSynaptomeCreate,
    user_context: UserContextWithProjectIdDep,
) -> SingleNeuronSynaptomeRead:
    return router_create_one(
        db=db,
        json_model=json_model,
        db_model_class=SingleNeuronSynaptome,
        authorized_project_id=user_context.project_id,
        response_schema_class=SingleNeuronSynaptomeRead,
    )


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
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    filter_model: Annotated[
        SingleNeuronSynaptomeFilter, FilterDepends(SingleNeuronSynaptomeFilter)
    ],
    search: str | None = None,
    with_facets: bool | None = None,  # noqa: FBT001
) -> ListResponse[SingleNeuronSynaptomeRead]:
    agent_alias = aliased(Agent, flat=True)
    me_model_alias = aliased(MEModel, flat=True)
    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "contribution": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
        "brain_region": {"id": BrainRegion.id, "label": BrainRegion.name},
        "me_model": {"id": me_model_alias.id, "label": me_model_alias.name},
    }

    filter_query = (
        constrain_to_accessible_entities(
            sa.select(SingleNeuronSynaptome),
            project_id=user_context.project_id,
        )
        .join(BrainRegion, SingleNeuronSynaptome.brain_region_id == BrainRegion.id)
        .outerjoin(Contribution, SingleNeuronSynaptome.id == Contribution.entity_id)
        .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
        .outerjoin(me_model_alias, SingleNeuronSynaptome.me_model_id == me_model_alias.id)
    )

    if search:
        filter_query = filter_query.where(SingleNeuronSynaptome.description_vector.match(search))

    filter_query = filter_model.filter(
        filter_query, aliases={Agent: agent_alias, MEModel: me_model_alias}
    )

    if with_facets:
        facets = _get_facets(
            db,
            filter_query,
            name_to_facet_query_params=name_to_facet_query_params,
            count_distinct_field=SingleNeuronSynaptome.id,
        )
    else:
        facets = None

    distinct_ids_subquery = (
        filter_model.sort(filter_query)
        .with_only_columns(SingleNeuronSynaptome)
        .distinct()
        .offset(pagination_request.offset)
        .limit(pagination_request.page_size)
    ).subquery("distinct_ids")

    data_query = (
        filter_model.sort(sa.Select(SingleNeuronSynaptome))  # sort without filtering
        .join(distinct_ids_subquery, SingleNeuronSynaptome.id == distinct_ids_subquery.c.id)
        .options(joinedload(SingleNeuronSynaptome.me_model).joinedload(MEModel.brain_region))
        .options(joinedload(SingleNeuronSynaptome.brain_region))
        .options(raiseload("*"))
    )

    # unique is needed b/c it contains results that include joined eager loads against collections
    data = db.execute(data_query).scalars().unique()

    total_items = db.execute(
        filter_query.with_only_columns(
            sa.func.count(sa.func.distinct(SingleNeuronSynaptome.id)).label("count")
        )
    ).scalar_one()

    response = ListResponse[SingleNeuronSynaptomeRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=facets,
    )

    return response
