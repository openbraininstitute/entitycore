import uuid
from functools import partial
from typing import TYPE_CHECKING, Annotated

import sqlalchemy as sa
from fastapi import Query
from sqlalchemy.orm import (
    aliased,
    joinedload,
    raiseload,
    selectinload,
)

from app.db.model import (
    Agent,
    Contribution,
    MeasurementAnnotation,
    MeasurementKind,
    ReconstructionMorphology,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import (
    FacetsDep,
    InBrainRegionDep,
    PaginationQuery,
    SearchDep,
)
from app.dependencies.db import SessionDep
from app.filters.morphology import MorphologyFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.queries.factory import query_params_factory
from app.schemas.morphology import (
    ReconstructionMorphologyAnnotationExpandedRead,
    ReconstructionMorphologyCreate,
    ReconstructionMorphologyRead,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.filters.base import Aliases


def _load_from_db(query: sa.Select, *, expand_measurement_annotation: bool = False) -> sa.Select:
    """Return the query with the required options to load the data."""
    query = query.options(
        joinedload(ReconstructionMorphology.brain_region),
        selectinload(ReconstructionMorphology.contributions).selectinload(Contribution.agent),
        selectinload(ReconstructionMorphology.contributions).selectinload(Contribution.role),
        joinedload(ReconstructionMorphology.mtypes),
        joinedload(ReconstructionMorphology.license),
        joinedload(ReconstructionMorphology.species, innerjoin=True),
        joinedload(ReconstructionMorphology.strain),
        selectinload(ReconstructionMorphology.assets),
        joinedload(ReconstructionMorphology.createdBy),
        joinedload(ReconstructionMorphology.updatedBy),
        raiseload("*"),
    )
    if expand_measurement_annotation:
        query = query.options(
            joinedload(ReconstructionMorphology.measurement_annotation)
            .selectinload(MeasurementAnnotation.measurement_kinds)
            .selectinload(MeasurementKind.measurement_items),
            joinedload(ReconstructionMorphology.measurement_annotation).contains_eager(
                MeasurementAnnotation.entity
            ),
        )
    return query


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    expand: Annotated[set[str] | None, Query()] = None,
) -> ReconstructionMorphologyRead | ReconstructionMorphologyAnnotationExpandedRead:
    if expand and "measurement_annotation" in expand:
        response_schema_class = ReconstructionMorphologyAnnotationExpandedRead
        apply_operations = partial(_load_from_db, expand_measurement_annotation=True)
    else:
        response_schema_class = ReconstructionMorphologyRead
        apply_operations = partial(_load_from_db, expand_measurement_annotation=False)
    return router_read_one(
        id_=id_,
        db=db,
        db_model_class=ReconstructionMorphology,
        authorized_project_id=user_context.project_id,
        response_schema_class=response_schema_class,
        apply_operations=apply_operations,
    )


def create_one(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    reconstruction: ReconstructionMorphologyCreate,
) -> ReconstructionMorphologyRead:
    return router_create_one(
        db=db,
        user_context=user_context,
        db_model_class=ReconstructionMorphology,
        json_model=reconstruction,
        response_schema_class=ReconstructionMorphologyRead,
    )


def read_many(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    morphology_filter: MorphologyFilterDep,
    search: SearchDep,
    with_facets: FacetsDep,
    in_brain_region: InBrainRegionDep,
) -> ListResponse[ReconstructionMorphologyRead]:
    agent_alias = aliased(Agent, flat=True)
    created_by_alias = aliased(Agent, flat=True)
    updated_by_alias = aliased(Agent, flat=True)
    aliases: Aliases = {
        Agent: {
            "contribution": agent_alias,
            "createdBy": created_by_alias,
            "updatedBy": updated_by_alias,
        },
    }
    facet_keys = [
        "brain_region",
        "species",
        "createdBy",
        "updatedBy",
        "contribution",
        "mtype",
        "strain",
    ]
    filter_keys = [
        *facet_keys,
        "measurement_annotation",
        "measurement_annotation.measurement_kind",
        "measurement_annotation.measurement_kind.measurement_item",
    ]
    name_to_facet_query_params, filter_joins = query_params_factory(
        db_model_class=ReconstructionMorphology,
        facet_keys=facet_keys,
        filter_keys=filter_keys,
        aliases=aliases,
    )
    return router_read_many(
        db=db,
        db_model_class=ReconstructionMorphology,
        authorized_project_id=user_context.project_id,
        with_search=search,
        with_in_brain_region=in_brain_region,
        facets=with_facets,
        aliases=aliases,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load_from_db,
        pagination_request=pagination_request,
        response_schema_class=ReconstructionMorphologyRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=morphology_filter,
        filter_joins=filter_joins,
    )
