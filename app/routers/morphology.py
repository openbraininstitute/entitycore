from fastapi import APIRouter

from typing import List, Optional
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.dependencies.db import get_db
from typing import Union
from app.schemas.morphology import (
    ReconstructionMorphologyRead,
    ReconstructionMorphologyExpand,
    ReconstructionMorphologyCreate,
)
from app.models.morphology import (
    ReconstructionMorphology,
)
from app.models.base import BrainLocation
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

router = APIRouter(
    prefix="/reconstruction_morphology",
    tags=["reconstruction_morphology"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{rm_id}",
    response_model=Union[ReconstructionMorphologyExpand, ReconstructionMorphologyRead],
)
async def read_reconstruction_morphology(
    rm_id: int, expand: Optional[str] = Query(None), db: Session = Depends(get_db)
):
    rm = (
        db.query(ReconstructionMorphology)
        .filter(ReconstructionMorphology.id == rm_id)
        .first()
    )

    if rm is None:
        raise HTTPException(
            status_code=404, detail="ReconstructionMorphology not found"
        )
    if expand and "morphology_feature_annotation" in expand:
        # res = (
        #     db.query(model.MorphologyFeatureAnnotation)
        #     .filter(
        #         model.MorphologyFeatureAnnotation.reconstruction_morphology_id == rm_id
        #     )
        #     .all()
        # )
        # if res:
        #     rm.morphology_feature_annotation = res[0]
        ret = ReconstructionMorphologyExpand.from_orm(rm).dict()
        return ret
    else:
        ret = ReconstructionMorphologyRead.model_validate(rm)
        # added back with None by the response_model
        return ret


@router.post("/", response_model=ReconstructionMorphologyRead)
def create_reconstruction_morphology(
    recontruction: ReconstructionMorphologyCreate, db: Session = Depends(get_db)
):
    brain_location = None
    if recontruction.brain_location:
        brain_location = BrainLocation(**recontruction.brain_location.dict())
    db_reconstruction_morphology = ReconstructionMorphology(
        name=recontruction.name,
        description=recontruction.description,
        brain_location=brain_location,
        brain_region_id=recontruction.brain_region_id,
        species_id=recontruction.species_id,
        strain_id=recontruction.strain_id,
        license_id=recontruction.license_id,
    )
    db.add(db_reconstruction_morphology)
    db.commit()
    db.refresh(db_reconstruction_morphology)
    return db_reconstruction_morphology


@router.get("/", response_model=List[ReconstructionMorphologyRead])
async def read_reconstruction_morphologies(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    rm = db.query(ReconstructionMorphology).offset(skip).limit(limit).all()
    return rm

# facet prototype
from app.models.base import Species, Strain
from sqlalchemy import func, select
from fastapi import Request
from sqlalchemy.orm import aliased


@router.get("/q/")
async def morphology_query(req: Request, session: Session = Depends(get_db)):
    # brain_region_id, species_id, strain_id
    args = req.query_params
    name_to_table = {
        "species": Species,
        "strain": Strain,
    }
    term = args.get("q")
    data_q = (
        select(
            ReconstructionMorphology.name,
            Species.name.label("species_name"),
            Strain.name.label("strain_name"),
        )
        .join(Species, ReconstructionMorphology.species_id == Species.id)
        .join(Strain, ReconstructionMorphology.strain_id == Strain.id)
        .filter(ReconstructionMorphology.morphology_description_vector.match(term))
    )
    for ty in name_to_table:
        if value := args.get(ty, None):
            table = name_to_table[ty]
            data_q = data_q.where(getattr(table, "name") == value)
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
                    getattr(ReconstructionMorphology, other_ty + "_id")
                    == other_types.id,
                ).where(other_types.name == value)
        facets[ty] = {r.name: r.count for r in facet_q.all()}
    res = {
        "data": [
            {"name": r.name, "species": r.species_name, "strain": r.strain_name}
            for r in session.execute(data_q)
        ],
        "facets": facets,
    }
    return JSONResponse(content=jsonable_encoder(res))
