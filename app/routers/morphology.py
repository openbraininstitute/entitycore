from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
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
def read_reconstruction_morphology(
    rm_id: int, expand: Annotated[str | None, Query(None)], db: SessionDep
):
    rm = db.query(ReconstructionMorphology).filter(ReconstructionMorphology.id == rm_id).first()

    if rm is None:
        raise HTTPException(status_code=404, detail="ReconstructionMorphology not found")

    if expand and "morphology_feature_annotation" in expand:
        ret = ReconstructionMorphologyExpand.model_validate(rm)
        return ret
    ret = ReconstructionMorphologyRead.model_validate(rm)
    # added back with None by the response_model
    return ret


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


@router.get("/", response_model=list[ReconstructionMorphologyRead])
def read_reconstruction_morphologies(
    morphology_filter: Annotated[MorphologyFilter, FilterDepends(MorphologyFilter)],
    db: SessionDep,
    skip: int = 0,
    limit: int = 10,
):
    query = db.query(ReconstructionMorphology)
    query = morphology_filter.filter(query)
    rms = morphology_filter.sort(query).offset(skip).limit(limit).all()
    return rms


@router.get("/q/")
def morphology_query(
    req: Request,
    session: SessionDep,
    term: Annotated[str | None, Query(None)],
    skip: int = 0,
    limit: int = 10,
):
    # brain_region_id, species_id, strain_id
    args = req.query_params
    name_to_table = {
        "species": Species,
        "strain": Strain,
    }
    facets = {}
    for ty in name_to_table:
        types = aliased(name_to_table[ty])
        facet_q = (
            session.query(types.name, func.count().label("count"))
            .join(
                ReconstructionMorphology,
                getattr(ReconstructionMorphology, ty + "_id") == types.id,
            )
            .filter(ReconstructionMorphology.morphology_description_vector.match(term))
            .group_by(types.name)
        )

        for other_ty in name_to_table:
            if value := args.get(other_ty, None):
                other_table = name_to_table[other_ty]
                other_types = aliased(other_table)
                facet_q = facet_q.join(
                    other_types,
                    getattr(ReconstructionMorphology, other_ty + "_id") == other_types.id,
                ).where(other_types.name == value)
        facets[ty] = {r.name: r.count for r in facet_q.all()}
    rms = (
        session.query(ReconstructionMorphology)
        .where(ReconstructionMorphology.morphology_description_vector.match(term))
        .offset(skip)
        .limit(limit)
        .all()
    )
    res = {
        "data": [ReconstructionMorphologyRead.model_validate(rm) for rm in rms],
        "facets": facets,
    }
    return JSONResponse(content=jsonable_encoder(res))
