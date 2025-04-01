import uuid
from typing import Annotated

import sqlalchemy as sa
from fastapi import APIRouter, Query
from fastapi_filter import FilterDepends
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
from app.dependencies.common import FacetQueryParams, PaginationQuery, _get_facets
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.morphology import MorphologyFilter
from app.schemas.morphology import (
    ReconstructionMorphologyAnnotationExpandedRead,
    ReconstructionMorphologyCreate,
    ReconstructionMorphologyRead,
)
from app.schemas.types import ListResponse, PaginationResponse

router = APIRouter(
    prefix="/reconstruction-morphology",
    tags=["reconstruction-morphology"],
)


@router.get(
    "/{id_}",
    response_model=ReconstructionMorphologyRead | ReconstructionMorphologyAnnotationExpandedRead,
)
def read_reconstruction_morphology(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
    expand: Annotated[set[str] | None, Query()] = None,
):
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


@router.post("", response_model=ReconstructionMorphologyRead)
def create_reconstruction_morphology(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    reconstruction: ReconstructionMorphologyCreate,
):
    db_rm = ReconstructionMorphology(
        name=reconstruction.name,
        description=reconstruction.description,
        location=reconstruction.location,
        brain_region_id=reconstruction.brain_region_id,
        species_id=reconstruction.species_id,
        strain_id=reconstruction.strain_id,
        license_id=reconstruction.license_id,
        authorized_project_id=user_context.project_id,
        authorized_public=reconstruction.authorized_public,
    )
    db.add(db_rm)
    db.commit()
    db.refresh(db_rm)

    return db_rm


@router.get("")
def morphology_query(
    *,
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
    morphology_filter: Annotated[MorphologyFilter, FilterDepends(MorphologyFilter)],
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
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=facets,
    )

    return response
