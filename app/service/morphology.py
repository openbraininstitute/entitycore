import uuid
from typing import TYPE_CHECKING, Annotated, cast

import sqlalchemy as sa
from fastapi import Query
from sqlalchemy.orm import (
    aliased,
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
from app.dependencies.common import PaginationQuery, _get_facets
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.morphology import MorphologyFilterDep
from app.queries.common import router_create_one
from app.schemas.morphology import (
    ReconstructionMorphologyAnnotationExpandedRead,
    ReconstructionMorphologyCreate,
    ReconstructionMorphologyRead,
)
from app.schemas.types import ListResponse, PaginationResponse

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
    search: str | None = None,
    with_facets: bool = False,
) -> ListResponse[ReconstructionMorphologyRead]:
    agent_alias = aliased(Agent, flat=True)
    name_to_facet_query_params: dict[str, FacetQueryParams] = {
        "mtype": {"id": MTypeClass.id, "label": MTypeClass.pref_label},
        "species": {"id": Species.id, "label": Species.name},
        "strain": {"id": Strain.id, "label": Strain.name},
        "contribution": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
    }

    filter_query = (
        constrain_to_accessible_entities(
            sa.select(ReconstructionMorphology), project_id=user_context.project_id
        )
        .join(Species, ReconstructionMorphology.species_id == Species.id)
        .outerjoin(Strain, ReconstructionMorphology.strain_id == Strain.id)
        .outerjoin(Contribution, ReconstructionMorphology.id == Contribution.entity_id)
        .outerjoin(agent_alias, Contribution.agent_id == agent_alias.id)
        .outerjoin(
            MTypeClassification, ReconstructionMorphology.id == MTypeClassification.entity_id
        )
        .outerjoin(MTypeClass, MTypeClass.id == MTypeClassification.mtype_class_id)
    )

    if search:
        filter_query = filter_query.where(ReconstructionMorphology.description_vector.match(search))

    filter_query = morphology_filter.filter(filter_query, aliases={Agent: agent_alias})

    if with_facets:
        facets = _get_facets(
            db,
            filter_query,
            name_to_facet_query_params=name_to_facet_query_params,
            count_distinct_field=ReconstructionMorphology.id,
        )
    else:
        facets = None

    distinct_ids_subquery = (
        morphology_filter.sort(filter_query)
        .with_only_columns(ReconstructionMorphology)
        .distinct()
        .offset(pagination_request.offset)
        .limit(pagination_request.page_size)
    ).subquery("distinct_ids")

    # TODO: load person.* and organization.* eagerly
    data_query = (
        morphology_filter.sort(sa.Select(ReconstructionMorphology))  # sort without filtering
        .join(distinct_ids_subquery, ReconstructionMorphology.id == distinct_ids_subquery.c.id)
        .options(joinedload(ReconstructionMorphology.species, innerjoin=True))
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

    # unique is needed b/c it contains results that include joined eager loads against collections
    data = db.execute(data_query).scalars().unique()

    total_items = db.execute(
        filter_query.with_only_columns(
            sa.func.count(sa.func.distinct(ReconstructionMorphology.id)).label("count")
        )
    ).scalar_one()

    response = ListResponse[ReconstructionMorphologyRead](
        data=cast("list[ReconstructionMorphologyRead]", data),
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=facets,
    )

    return response
