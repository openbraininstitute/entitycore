from typing import Annotated

from fastapi import APIRouter
from fastapi_filter import FilterDepends
from sqlalchemy import func
from sqlalchemy.orm import aliased, joinedload

from app.db.auth import constrain_to_accessible_entities
from app.db.model import (
    Agent,
    Base,
    BrainLocation,
    Contribution,
    ReconstructionMorphology,
    Species,
    Strain,
)
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.morphology import MorphologyFilter
from app.routers.types import Facet, Facets, ListResponse, Pagination
from app.schemas.morphology import (
    ReconstructionMorphologyAnnotationExpandedRead,
    ReconstructionMorphologyCreate,
    ReconstructionMorphologyRead,
)

router = APIRouter(
    prefix="/reconstruction_morphology",
    tags=["reconstruction_morphology"],
)


@router.get(
    "/{rm_id}",
    response_model=ReconstructionMorphologyRead | ReconstructionMorphologyAnnotationExpandedRead,
)
def read_reconstruction_morphology(
    db: SessionDep,
    rm_id: int,
    project_context: VerifiedProjectContextHeader,
    expand: str | None = None,
):
    with ensure_result(error_message="ReconstructionMorphology not found"):
        query = constrain_to_accessible_entities(
            db.query(ReconstructionMorphology), project_context.project_id
        ).filter(ReconstructionMorphology.id == rm_id)

        if expand and "morphology_feature_annotation" in expand:
            query = query.options(
                joinedload(ReconstructionMorphology.morphology_feature_annotation)
            )

        query = (
            query.options(joinedload(ReconstructionMorphology.brain_location))
            .options(joinedload(ReconstructionMorphology.brain_region))
            .options(joinedload(ReconstructionMorphology.contributors))
            .options(joinedload(ReconstructionMorphology.license))
            .options(joinedload(ReconstructionMorphology.species))
            .options(joinedload(ReconstructionMorphology.strain))
        )

        row = query.one()

    if expand and "morphology_feature_annotation" in expand:
        return ReconstructionMorphologyAnnotationExpandedRead.model_validate(row)

    # added back with None by the response_model
    return ReconstructionMorphologyRead.model_validate(row)


@router.post("/", response_model=ReconstructionMorphologyRead)
def create_reconstruction_morphology(
    project_context: VerifiedProjectContextHeader,
    reconstruction: ReconstructionMorphologyCreate,
    db: SessionDep,
):
    brain_location = None

    if reconstruction.brain_location:
        brain_location = BrainLocation(**reconstruction.brain_location.model_dump())

    db_rm = ReconstructionMorphology(
        name=reconstruction.name,
        description=reconstruction.description,
        brain_location=brain_location,
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
    db: SessionDep,
    query,
    name_to_table: dict[str, type[Base]],
) -> Facets:
    facets = {}

    for ty, table in name_to_table.items():
        types = aliased(table)
        # TODO: this should be migrated to sqlalchemy v2.0 style:
        # https://github.com/openbraininstitute/entitycore/pull/11#discussion_r1935703476
        facet_q = (
            db.query(types)
            .join(query.subquery())
            .add_columns(func.count().label("count"))
            .group_by(types)  # type: ignore[arg-type]
        )
        facets[ty] = [
            Facet(id=r.id, label=r.name, type=ty, count=count) for r, count in facet_q.all()
        ]

    return facets


def _get_facet_contributor(
    db: SessionDep,
    query,
) -> list[Facet]:
    subq = query.subquery()
    facet_q = (
        db.query(Agent)
        .join(Contribution)
        .join(subq, Contribution.entity_id == subq.c.id)
        .add_columns(func.count().label("count"))
        .group_by(Agent)  # type: ignore[arg-type]
    )

    return [
        Facet(id=r.id, label=r.pref_label, type=r.type, count=count) for r, count in facet_q.all()
    ]


@router.get("/", response_model=ListResponse[ReconstructionMorphologyRead])
def morphology_query(
    db: SessionDep,
    project_context: VerifiedProjectContextHeader,
    morphology_filter: Annotated[MorphologyFilter, FilterDepends(MorphologyFilter)],
    search: str | None = None,
    page: int = 0,
    page_size: int = 10,
):
    name_to_table = {
        "species": Species,
        "strain": Strain,
    }

    query = db.query(ReconstructionMorphology)
    query = constrain_to_accessible_entities(query, project_context.project_id)
    query = query.outerjoin(Species).outerjoin(Strain)

    if search:
        query = query.filter(ReconstructionMorphology.morphology_description_vector.match(search))

    query = morphology_filter.filter(query)

    facets = _get_facets(db, query, name_to_table)

    facets["contributors"] = _get_facet_contributor(db, query)

    query = (
        query.options(joinedload(ReconstructionMorphology.brain_location))
        .options(joinedload(ReconstructionMorphology.brain_region))
        .options(joinedload(ReconstructionMorphology.contributors))
        .options(joinedload(ReconstructionMorphology.license))
        .options(joinedload(ReconstructionMorphology.species))
        .options(joinedload(ReconstructionMorphology.strain))
    )

    response = ListResponse[ReconstructionMorphologyRead](
        data=morphology_filter.sort(query).offset(page * page_size).limit(page_size).all(),
        pagination=Pagination(page=page, page_size=page_size, total_items=query.count()),
        facets=facets,
    )

    return response
