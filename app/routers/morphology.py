from typing import Annotated

from fastapi import APIRouter, HTTPException, Request
from fastapi_filter import FilterDepends
from sqlalchemy import func
from sqlalchemy.orm import aliased

from app.db.model import (
    BrainLocation,
    ReconstructionMorphology,
    Species,
    Strain,
)
from app.dependencies.db import SessionDep
from app.filters.morphology import MorphologyFilter
from app.routers.types import ListResponse, Pagination
from app.schemas.morphology import (
    ReconstructionMorphologyCreate,
    ReconstructionMorphologyExpand,
    ReconstructionMorphologyRead,
)

router = APIRouter(
    prefix="/reconstruction_morphology",
    tags=["reconstruction_morphology"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{rm_id}",
    response_model=ReconstructionMorphologyExpand | ReconstructionMorphologyRead,
)
def read_reconstruction_morphology(db: SessionDep, rm_id: int, expand: str | None = None):
    rm = db.query(ReconstructionMorphology).filter(ReconstructionMorphology.id == rm_id).first()

    if rm is None:
        raise HTTPException(status_code=404, detail="ReconstructionMorphology not found")

    if expand and "morphology_feature_annotation" in expand:
        return ReconstructionMorphologyExpand.model_validate(rm)

    # added back with None by the response_model
    return ReconstructionMorphologyRead.model_validate(rm)


@router.post("/", response_model=ReconstructionMorphologyRead)
def create_reconstruction_morphology(
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
    )
    db.add(db_reconstruction_morphology)
    db.commit()
    db.refresh(db_reconstruction_morphology)
    return db_reconstruction_morphology


@router.get("/", response_model=ListResponse[ReconstructionMorphologyRead])
def morphology_query(
    request: Request,
    db: SessionDep,
    morphology_filter: Annotated[MorphologyFilter, FilterDepends(MorphologyFilter)],
    search: str | None = None,
    skip: int = 0,
    limit: int = 10,
):
    name_to_table = {
        "species": Species,
        "strain": Strain,
    }

    if search is None and not any(ty in request.query_params for ty in name_to_table):
        query = db.query(ReconstructionMorphology)
        query = morphology_filter.filter(query)
        response = ListResponse[ReconstructionMorphologyRead](
            data=morphology_filter.sort(query).offset(skip).limit(limit).all(),
            pagination=Pagination(page=0, limit=0, total=0),
        )
    else:
        facets = {}
        for ty, table in name_to_table.items():
            types = aliased(table)
            facet_q = (
                db.query(types.name, func.count().label("count"))  # type: ignore[attr-defined]
                .join(
                    ReconstructionMorphology,
                    getattr(ReconstructionMorphology, ty + "_id") == types.id,  # type: ignore[attr-defined]
                )
                .filter(ReconstructionMorphology.morphology_description_vector.match(search))
                .group_by(types.name)  # type: ignore[attr-defined]
            )

            for other_ty, other_table in name_to_table.items():
                if value := request.query_params.get(other_ty, None):
                    other_types = aliased(other_table)
                    facet_q = facet_q.join(
                        other_types,
                        getattr(ReconstructionMorphology, other_ty + "_id") == other_types.id,  # type: ignore[attr-defined]
                    ).where(other_types.name == value)  # type: ignore[attr-defined]
            facets[ty] = {r.name: r.count for r in facet_q.all()}

        rms = (
            db.query(ReconstructionMorphology)
            .where(ReconstructionMorphology.morphology_description_vector.match(search))
            .offset(skip)
            .limit(limit)
            .all()
        )

        response = ListResponse[ReconstructionMorphologyRead](
            data=[ReconstructionMorphologyRead.model_validate(rm) for rm in rms],
            pagination=Pagination(page=0, limit=0, total=0),
            facets=facets,
        )
    return response
