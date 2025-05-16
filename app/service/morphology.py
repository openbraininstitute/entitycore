import uuid
from functools import partial
from typing import Annotated

import sqlalchemy as sa
from fastapi import Query
from sqlalchemy.orm import (
    joinedload,
    raiseload,
    selectinload,
)

from app.db.model import (
    Agent,
    BrainRegion,
    Contribution,
    MeasurementAnnotation,
    MeasurementItem,
    MeasurementKind,
    MTypeClass,
    MTypeClassification,
    ReconstructionMorphology,
    Species,
    Strain,
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
from app.filters.morphology import MorphologyFilterDep
from app.queries.common import router_create_one, router_read_many, router_read_one
from app.schemas.morphology import (
    ReconstructionMorphologyAnnotationExpandedRead,
    ReconstructionMorphologyCreate,
    ReconstructionMorphologyRead,
)
from app.schemas.types import ListResponse


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
        db_model_class=ReconstructionMorphology,
        authorized_project_id=user_context.project_id,
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
    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "brain_region": {"id": BrainRegion.id, "label": BrainRegion.name},
        "mtype": {"id": MTypeClass.id, "label": MTypeClass.pref_label},
        "species": {"id": Species.id, "label": Species.name},
        "strain": {"id": Strain.id, "label": Strain.name},
        "contribution": {
            "id": Agent.id,
            "label": Agent.pref_label,
            "type": Agent.type,
        },
    }
    filter_joins = {
        "brain_region": lambda q: q.join(
            BrainRegion, ReconstructionMorphology.brain_region_id == BrainRegion.id
        ),
        "species": lambda q: q.join(Species, ReconstructionMorphology.species_id == Species.id),
        "strain": lambda q: q.outerjoin(Strain, ReconstructionMorphology.strain_id == Strain.id),
        "contribution": lambda q: q.outerjoin(
            Contribution, ReconstructionMorphology.id == Contribution.entity_id
        ).outerjoin(Agent, Contribution.agent_id == Agent.id),
        "mtype": lambda q: q.outerjoin(
            MTypeClassification, ReconstructionMorphology.id == MTypeClassification.entity_id
        ).outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id),
        "measurement_annotation": lambda q: q.outerjoin(
            MeasurementAnnotation, MeasurementAnnotation.entity_id == ReconstructionMorphology.id
        ),
        "measurement_annotation.measurement_kind": lambda q: q.outerjoin(
            MeasurementKind,
            MeasurementKind.measurement_annotation_id == MeasurementAnnotation.id,
        ),
        "measurement_annotation.measurement_kind.measurement_item": lambda q: q.outerjoin(
            MeasurementItem, MeasurementItem.measurement_kind_id == MeasurementKind.id
        ),
    }
    return router_read_many(
        db=db,
        db_model_class=ReconstructionMorphology,
        authorized_project_id=user_context.project_id,
        with_search=search,
        with_in_brain_region=in_brain_region,
        facets=with_facets,
        aliases=None,
        apply_filter_query_operations=None,
        apply_data_query_operations=_load_from_db,
        pagination_request=pagination_request,
        response_schema_class=ReconstructionMorphologyRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=morphology_filter,
        filter_joins=filter_joins,
    )
