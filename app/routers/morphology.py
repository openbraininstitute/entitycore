from typing import Annotated

import sqlalchemy as sa
from fastapi import APIRouter
from fastapi_filter import FilterDepends
from sqlalchemy import func
from sqlalchemy.orm import aliased, joinedload

from app.db.auth import constrain_to_accessible_entities
from app.db.model import (
    Base,
    BrainLocation,
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
    ReconstructionMorphologyCreate,
    ReconstructionMorphologyExpand,
    ReconstructionMorphologyRead,
)

router = APIRouter(
    prefix="/reconstruction_morphology",
    tags=["reconstruction_morphology"],
)


@router.get(
    "/{rm_id}",
    response_model=ReconstructionMorphologyExpand | ReconstructionMorphologyRead,
)
def read_reconstruction_morphology(
    db: SessionDep,
    rm_id: int,
    project_context: VerifiedProjectContextHeader,
    expand: str | None = None,
):
    with ensure_result(error_message="ReconstructionMorphology not found"):
        rm = (
            constrain_to_accessible_entities(
                db.query(ReconstructionMorphology), project_context.project_id
            )
            .filter(ReconstructionMorphology.id == rm_id)
            .one()
        )

    if expand and "morphology_feature_annotation" in expand:
        return ReconstructionMorphologyExpand.model_validate(rm)

    # added back with None by the response_model
    return ReconstructionMorphologyRead.model_validate(rm)


@router.post("/", response_model=ReconstructionMorphologyRead)
def create_reconstruction_morphology(
    project_context: VerifiedProjectContextHeader,
    reconstruction: ReconstructionMorphologyCreate,
    db: SessionDep,
):
    brain_location = None

    if reconstruction.brain_location:
        brain_location = BrainLocation(**reconstruction.brain_location.model_dump())

    db_reconstruction_morphology = ReconstructionMorphology(
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
    db.add(db_reconstruction_morphology)
    db.commit()
    db.refresh(db_reconstruction_morphology)
    return db_reconstruction_morphology


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

    query = (
        constrain_to_accessible_entities(
            sa.select(ReconstructionMorphology), project_context.project_id
        )
        .outerjoin(Strain, ReconstructionMorphology.strain_id == Strain.id)
        .outerjoin(Species, ReconstructionMorphology.species_id == Species.id)
    )

    if search:
        query = query.where(ReconstructionMorphology.morphology_description_vector.match(search))

    query = morphology_filter.filter(query)

    facets = _get_facets(db, query, name_to_table)

    query = (
        query.options(joinedload(ReconstructionMorphology.license))
        .options(joinedload(ReconstructionMorphology.species))
        .options(joinedload(ReconstructionMorphology.brain_region))
        .options(joinedload(ReconstructionMorphology.brain_location))
        .options(joinedload(ReconstructionMorphology.strain))
    )

    data = db.execute(
        morphology_filter.sort(query).offset(page * page_size).limit(page_size)
    ).scalars()
    total_items = db.execute(query.with_only_columns(func.count())).scalar_one()
    response = ListResponse[ReconstructionMorphologyRead](
        data=data,
        pagination=Pagination(page=page, page_size=page_size, total_items=total_items),
        facets=facets,
    )

    return response
