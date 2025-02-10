from typing import Annotated

from fastapi import APIRouter
from fastapi_filter import FilterDepends
from sqlalchemy import func
from sqlalchemy.orm import aliased, joinedload

from app.db.model import (
    Base,
    BrainLocation,
    Contribution,
    ReconstructionMorphology,
    Species,
    Strain,
)
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
def read_reconstruction_morphology(db: SessionDep, rm_id: int, expand: str | None = None):
    with ensure_result(error_message="ReconstructionMorphology not found"):
        query = db.query(ReconstructionMorphology)
        if expand:
            if "morphology_feature_annotation" in expand:
                query = query.filter(ReconstructionMorphology.id == rm_id)
            if "contributions" in expand:
                query = query.filter(Contribution.id == rm_id)

        row = query.one()

    if expand and "morphology_feature_annotation" in expand:
        return ReconstructionMorphologyAnnotationExpandedRead.model_validate(row)

    # added back with None by the response_model
    return ReconstructionMorphologyRead.model_validate(row)


@router.post("/", response_model=ReconstructionMorphologyRead)
def create_reconstruction_morphology(
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
        facets[ty] = [Facet(id=r.id, label=r.name, count=count) for r, count in facet_q.all()]

    return facets


@router.get("/", response_model=ListResponse[ReconstructionMorphologyRead])
def morphology_query(
    db: SessionDep,
    morphology_filter: Annotated[MorphologyFilter, FilterDepends(MorphologyFilter)],
    search: str | None = None,
    page: int = 0,
    page_size: int = 10,
):
    name_to_table = {
        "species": Species,
        "strain": Strain,
    }

    query = db.query(ReconstructionMorphology).outerjoin(Species).outerjoin(Strain)

    if search:
        query = query.filter(ReconstructionMorphology.morphology_description_vector.match(search))

    query = morphology_filter.filter(query)

    facets = _get_facets(db, query, name_to_table)

    query = (
        query.options(joinedload(ReconstructionMorphology.license))
        .options(joinedload(ReconstructionMorphology.species))
        .options(joinedload(ReconstructionMorphology.brain_region))
        .options(joinedload(ReconstructionMorphology.brain_location))
    )

    response = ListResponse[ReconstructionMorphologyRead](
        data=morphology_filter.sort(query).offset(page * page_size).limit(page_size).all(),
        pagination=Pagination(page=page, page_size=page_size, total_items=query.count()),
        facets=facets,
    )

    return response
