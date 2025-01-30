from pathlib import Path

from fastapi import APIRouter, Response

router = APIRouter(
    prefix="/brain-regions",
    tags=["brain-region"],
    responses={404: {"description": "Not found"}},
)


# from app.db.model import BrainRegion
# from app.dependencies.db import SessionDep
# from app.schemas.base import (
#    BrainRegionCreate,
# )
# from app.schemas.morphology import (
#    BrainRegionRead,
# )
# @router.post("/", response_model=BrainRegionRead)
# def create_brain_region(brain_region: BrainRegionCreate, db: SessionDep):
#    db_brain_region = BrainRegion(ontology_id=brain_region.ontology_id, name=brain_region.name)
#    db.add(db_brain_region)
#    db.commit()
#    db.refresh(db_brain_region)
#    return db_brain_region

HIERARCHY = (Path(__file__).parent.parent / "static/brain-regions-tree.json").open().read()


@router.get("/")
def get() -> Response:
    return Response(content=HIERARCHY, media_type="application/json")
