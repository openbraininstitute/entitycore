from fastapi import APIRouter

from app.db.model import BrainRegion
from app.dependencies.db import SessionDep
from app.schemas.base import (
    BrainRegionCreate,
)
from app.schemas.morphology import (
    BrainRegionRead,
)

router = APIRouter(
    prefix="/brain_region",
    tags=["brain_region"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=BrainRegionRead)
def create_brain_region(brain_region: BrainRegionCreate, db: SessionDep):
    db_brain_region = BrainRegion(ontology_id=brain_region.ontology_id, name=brain_region.name)
    db.add(db_brain_region)
    db.commit()
    db.refresh(db_brain_region)
    return db_brain_region
