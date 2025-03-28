from pathlib import Path

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from app.db.model import BrainRegion
from app.dependencies.auth import user_with_service_admin_role
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.base import BrainRegionCreate, BrainRegionRead

HIERARCHY = (Path(__file__).parent.parent / "static/brain-regions-tree.json").open().read()


router = APIRouter(
    prefix="/brain-region",
    tags=["brain-region"],
)


def get_region_tree(db, start_id=None):
    query = sa.text("""
        WITH RECURSIVE region_tree AS (
            SELECT id, name, acronym, children, 1 as level
            FROM brain_region
            WHERE id = :start_id

            UNION ALL

            SELECT br.id, br.name, br.acronym, br.children, rt.level + 1
            FROM brain_region br
            INNER JOIN region_tree rt ON br.id = ANY(rt.children)
        )
        SELECT * FROM region_tree;
    """)

    result = db.execute(query, {"start_id": start_id}).fetchall()
    return result


@router.get("")
def get(*, db: SessionDep, flat: bool = False) -> Response:
    response: Response
    if flat:
        # TODO: this depends on 997 existing; which is bad
        # the return format isn't good, but this can be decided in the future
        response = JSONResponse(content=[tuple(r) for r in get_region_tree(db, start_id=997)])
    else:
        # return the old style DKE hierarchy
        response = Response(content=HIERARCHY, media_type="application/json")
    return response


@router.get("/{id_}", response_model=BrainRegionRead)
def read_brain_region(db: SessionDep, id_: int):
    with ensure_result(error_message="Brain region not found"):
        stmt = sa.select(BrainRegion).filter(BrainRegion.id == id_)
        row = db.execute(stmt).scalar_one()
    return BrainRegionRead.model_validate(row)


@router.post(
    "", dependencies=[Depends(user_with_service_admin_role)], response_model=BrainRegionRead
)
def create_brain_region(brain_region: BrainRegionCreate, db: SessionDep):
    row = BrainRegion(**brain_region.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
