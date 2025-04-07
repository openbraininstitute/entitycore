import uuid
from typing import TYPE_CHECKING, Annotated

import sqlalchemy as sa
from fastapi import Query
from sqlalchemy.orm import (
    joinedload,
    raiseload,
    selectinload,
)

from app.db.auth import constrain_to_accessible_entities
from app.db.model import (
    Agent,
    Contribution,
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MTypeClass,
    MTypeClassification,
    ReconstructionMorphology,
    Species,
    Strain,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import FacetsDep, PaginationQuery, SearchDep
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.morphology import MorphologyFilterDep
from app.queries.common import router_create_one, router_read_many
from app.schemas.morphology import (
    ReconstructionMorphologyAnnotationExpandedRead,
    ReconstructionMorphologyCreate,
    ReconstructionMorphologyRead,
)
from app.schemas.types import ListResponse

if TYPE_CHECKING:
    from app.queries.common import FacetQueryParams


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    expand: Annotated[set[str] | None, Query()] = None,
) -> ReconstructionMorphologyRead | ReconstructionMorphologyAnnotationExpandedRead:
    with ensure_result(error_message="ReconstructionMorphology not found"):
        query = constrain_to_accessible_entities(
            sa.select(ReconstructionMorphology), user_context.project_id
        ).filter(ReconstructionMorphology.id == id_)

        if expand and "morphology_feature_annotation" in expand:
            query = query.options(
                joinedload(ReconstructionMorphology.morphology_feature_annotation)
                .selectinload(MorphologyFeatureAnnotation.measurements)
                .selectinload(MorphologyMeasurement.measurement_serie)
            )

        query = (
            query.options(joinedload(ReconstructionMorphology.brain_region))
            .options(
                selectinload(ReconstructionMorphology.contributions).selectinload(
                    Contribution.agent
                )
            )
            .options(
                selectinload(ReconstructionMorphology.contributions).selectinload(Contribution.role)
            )
            .options(joinedload(ReconstructionMorphology.mtypes))
            .options(joinedload(ReconstructionMorphology.license))
            .options(joinedload(ReconstructionMorphology.species))
            .options(joinedload(ReconstructionMorphology.strain))
            .options(selectinload(ReconstructionMorphology.assets))
            .options(raiseload("*"))
        )

        row = db.execute(query).unique().scalar_one()

    if expand and "morphology_feature_annotation" in expand:
        return ReconstructionMorphologyAnnotationExpandedRead.model_validate(row)

    # added back with None by the response_model
    return ReconstructionMorphologyRead.model_validate(row)


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
) -> ListResponse[ReconstructionMorphologyRead]:
    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "mtype": {"id": MTypeClass.id, "label": MTypeClass.pref_label},
        "species": {"id": Species.id, "label": Species.name},
        "strain": {"id": Strain.id, "label": Strain.name},
        "contribution": {
            "id": Agent.id,
            "label": Agent.pref_label,
            "type": Agent.type,
        },
    }

    filter_query_ops = lambda q: (
        q.join(Species, ReconstructionMorphology.species_id == Species.id)
        .outerjoin(Strain, ReconstructionMorphology.strain_id == Strain.id)
        .outerjoin(Contribution, ReconstructionMorphology.id == Contribution.entity_id)
        .outerjoin(Agent, Contribution.agent_id == Agent.id)
        .outerjoin(
            MTypeClassification, ReconstructionMorphology.id == MTypeClassification.entity_id
        )
        .outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id)
    )

    # TODO: load person.* and organization.* eagerly
    data_query_ops = lambda q: (
        q.options(joinedload(ReconstructionMorphology.species, innerjoin=True))
        .options(joinedload(ReconstructionMorphology.strain))
        .options(
            selectinload(ReconstructionMorphology.contributions).selectinload(Contribution.agent)
        )
        .options(
            selectinload(ReconstructionMorphology.contributions).selectinload(Contribution.role)
        )
        .options(joinedload(ReconstructionMorphology.mtypes))
        .options(joinedload(ReconstructionMorphology.brain_region))
        .options(joinedload(ReconstructionMorphology.license))
        .options(selectinload(ReconstructionMorphology.assets))
        .options(raiseload("*"))
    )

    return router_read_many(
        db=db,
        db_model_class=ReconstructionMorphology,
        authorized_project_id=user_context.project_id,
        with_search=search,
        facets=with_facets,
        aliases=None,
        apply_filter_query_operations=filter_query_ops,
        apply_data_query_operations=data_query_ops,
        pagination_request=pagination_request,
        response_schema_class=ReconstructionMorphologyRead,
        name_to_facet_query_params=name_to_facet_query_params,
        filter_model=morphology_filter,
    )
