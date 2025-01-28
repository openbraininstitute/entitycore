from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi_filter import FilterDepends
from sqlalchemy import func
from sqlalchemy.orm import aliased

from app.db.authorization import constrain_query_to_members, raise_if_unauthorized
from app.db.model import (
    BrainLocation,
    ReconstructionMorphology,
    Species,
    Strain,
)
from app.dependencies.db import SessionDep
from app.filters.morphology import MorphologyFilter
from app.schemas.base import ProjectContext
from app.schemas.morphology import (
    ReconstructionMorphologyCreate,
    ReconstructionMorphologyExpand,
    ReconstructionMorphologyRead,
)


ProjectContextHeader = Annotated[ProjectContext, Header()]


router = APIRouter(
    prefix="/reconstruction_morphology",
    tags=["reconstruction_morphology"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{rm_id}",
    response_model=ReconstructionMorphologyExpand | ReconstructionMorphologyRead,
)
def read_reconstruction_morphology(project_context: ProjectContextHeader, db: SessionDep, rm_id: int, expand: str | None = None):
    rm = (constrain_query_to_members(db.query(ReconstructionMorphology),
                                     project_context.project_id)
          .filter(ReconstructionMorphology.id == rm_id)
          .first()
          )

    if rm is None:
        raise HTTPException(status_code=404, detail="ReconstructionMorphology not found")

    if expand and "morphology_feature_annotation" in expand:
        return ReconstructionMorphologyExpand.model_validate(rm)

    # added back with None by the response_model
    return ReconstructionMorphologyRead.model_validate(rm)


@router.post("/", response_model=ReconstructionMorphologyRead)
def create_reconstruction_morphology(
    project_context: ProjectContextHeader,
    reconstruction: ReconstructionMorphologyCreate,
    db: SessionDep,
):
    brain_location = None

    if reconstruction.brain_location:
        brain_location = BrainLocation(**reconstruction.brain_location.model_dump())

    if reconstruction.authorized_project_id is None:
        reconstruction.authorized_project_id = project_context.project_id

    raise_if_unauthorized(reconstruction.authorized_project_id)

    db_reconstruction_morphology = ReconstructionMorphology(
        name=reconstruction.name,
        description=reconstruction.description,
        brain_location=brain_location,
        brain_region_id=reconstruction.brain_region_id,
        species_id=reconstruction.species_id,
        strain_id=reconstruction.strain_id,
        license_id=reconstruction.license_id,
        authorized_project_id = reconstruction.authorized_project_id
    )
    db.add(db_reconstruction_morphology)
    db.commit()
    db.refresh(db_reconstruction_morphology)
    return db_reconstruction_morphology


@router.get("/", response_model=list[ReconstructionMorphologyRead])
def read_reconstruction_morphologies(
    project_context: ProjectContextHeader,
    morphology_filter: Annotated[MorphologyFilter, FilterDepends(MorphologyFilter)],
    db: SessionDep,
    skip: int = 0,
    limit: int = 10,
):
    query = db.query(ReconstructionMorphology)
    query = constrain_query_to_members(query, project_context.project_id)
    query = morphology_filter.filter(query)
    return morphology_filter.sort(query).offset(skip).limit(limit).all()


@router.get("/q/")
def morphology_query(
    req: Request,
    session: SessionDep,
    term: str | None = None,
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
    for ty, table in name_to_table.items():
        types = aliased(table)
        facet_q = (
            session.query(types.name, func.count().label("count"))  # type: ignore[attr-defined]
            .join(
                ReconstructionMorphology,
                getattr(ReconstructionMorphology, ty + "_id") == types.id,  # type: ignore[attr-defined]
            )
            .filter(ReconstructionMorphology.morphology_description_vector.match(term))
            .group_by(types.name)  # type: ignore[attr-defined]
        )

        for other_ty, other_table in name_to_table.items():
            if value := args.get(other_ty, None):
                other_types = aliased(other_table)
                facet_q = facet_q.join(
                    other_types,
                    getattr(ReconstructionMorphology, other_ty + "_id") == other_types.id,  # type: ignore[attr-defined]
                ).where(other_types.name == value)  # type: ignore[attr-defined]
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
