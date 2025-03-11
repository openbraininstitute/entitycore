from typing import Annotated, NotRequired, TypedDict

import sqlalchemy as sa
from fastapi import APIRouter
from fastapi_filter import FilterDepends
from sqlalchemy.orm import (
    InstrumentedAttribute,
    Session,
    aliased,
    joinedload,
    raiseload,
)
from sqlalchemy import Select

from app.db.auth import constrain_to_accessible_entities
from app.db.model import (
    Agent,
    Contribution,
    MTypeClass,
    MTypeClassification,
    ReconstructionMorphology,
    Species,
    Strain,
)
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.morphology import MorphologyFilter
from app.schemas.morphology import (
    ReconstructionMorphologyAnnotationExpandedRead,
    ReconstructionMorphologyCreate,
    ReconstructionMorphologyRead,
)
from app.schemas.types import Facet, Facets, ListResponse, PaginationResponse

router = APIRouter(
    prefix="/reconstruction-morphology",
    tags=["reconstruction-morphology"],
)


class FacetQueryParams(TypedDict):
    id: InstrumentedAttribute[int]
    label: InstrumentedAttribute[str]
    type: NotRequired[InstrumentedAttribute[str]]


@router.get(
    "/{id_}",
    response_model=ReconstructionMorphologyRead | ReconstructionMorphologyAnnotationExpandedRead,
)
def read_reconstruction_morphology(
    db: SessionDep,
    id_: int,
    project_context: VerifiedProjectContextHeader,
    expand: str | None = None,
):
    with ensure_result(error_message="ReconstructionMorphology not found"):
        query = constrain_to_accessible_entities(
            sa.select(ReconstructionMorphology), project_context.project_id
        ).filter(ReconstructionMorphology.id == id_)

        if expand and "morphology_feature_annotation" in expand:
            query = query.options(
                joinedload(ReconstructionMorphology.morphology_feature_annotation)
            )

        query = (
            query.options(joinedload(ReconstructionMorphology.brain_region))
            .options(joinedload(ReconstructionMorphology.contributions))
            .options(joinedload(ReconstructionMorphology.license))
            .options(joinedload(ReconstructionMorphology.species))
            .options(joinedload(ReconstructionMorphology.strain))
        )

        row = db.execute(query).unique().scalar_one()

    if expand and "morphology_feature_annotation" in expand:
        return ReconstructionMorphologyAnnotationExpandedRead.model_validate(row)

    # added back with None by the response_model
    return ReconstructionMorphologyRead.model_validate(row)


@router.post("", response_model=ReconstructionMorphologyRead)
def create_reconstruction_morphology(
    project_context: VerifiedProjectContextHeader,
    reconstruction: ReconstructionMorphologyCreate,
    db: SessionDep,
):
    db_rm = ReconstructionMorphology(
        name=reconstruction.name,
        description=reconstruction.description,
        location=reconstruction.location,
        brain_region_id=reconstruction.brain_region_id,
        species_id=reconstruction.species_id,
        strain_id=reconstruction.strain_id,
        license_id=reconstruction.license_id,
        authorized_project_id=project_context.project_id,
        authorized_public=reconstruction.authorized_public,
    )
    db.add(db_rm)
    db.commit()
    db.refresh(db_rm)

    return db_rm


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
def morphology_query(
    *,
    db: SessionDep,
    project_context: VerifiedProjectContextHeader,
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
        "contributions": {
            "id": agent_alias.id,
            "label": agent_alias.pref_label,
            "type": agent_alias.type,
        },
    }

    filter_query = (
        constrain_to_accessible_entities(
            sa.select(ReconstructionMorphology), project_id=project_context.project_id
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
        filter_query = filter_query.where(
            ReconstructionMorphology.morphology_description_vector.match(search)
        )

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

    # TODO: load person.* and organization.* eagerly
    data_query = (
        morphology_filter.sort(filter_query)
        .distinct(ReconstructionMorphology.id)
        .offset(pagination_request.offset)
        .limit(pagination_request.page_size)
        .options(joinedload(ReconstructionMorphology.species, innerjoin=True))
        .options(joinedload(ReconstructionMorphology.strain))
        .options(joinedload(ReconstructionMorphology.contributions).joinedload(Contribution.agent))
        .options(joinedload(ReconstructionMorphology.contributions).joinedload(Contribution.role))
        .options(joinedload(ReconstructionMorphology.mtype))
        .options(joinedload(ReconstructionMorphology.brain_region))
        .options(joinedload(ReconstructionMorphology.license))
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
