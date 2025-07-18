"""Entity router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.db.utils import EntityTypeWithBrainRegion
from app.dependencies.auth import AuthHeader, UserContextDep
from app.dependencies.common import InBrainRegionDep
from app.dependencies.db import SessionDep
from app.schemas.entity import EntityCountRead, EntityRead
from app.service import entity as entity_service

router = APIRouter(
    prefix="/entity",
    tags=["entity"],
)


@router.get("/counts")
def count_entities_by_type(
    user_context: UserContextDep,
    db: SessionDep,
    types: Annotated[
        list[EntityTypeWithBrainRegion], Query(min_length=1, description="Entity types with count")
    ],
    in_brain_region: InBrainRegionDep,
) -> EntityCountRead:
    """Count entities by their types.

    Returns the count of entities for each requested entity type that the user has access to.
    """
    return entity_service.count_entities_by_type(
        user_context=user_context,
        db=db,
        entity_types=types,
        in_brain_region=in_brain_region,
    )


@router.get("/{id_}", response_model=EntityRead)
def read_one(
    id_: UUID,
    db: SessionDep,
    token: Annotated[HTTPAuthorizationCredentials | None, Depends(AuthHeader)],
    request: Request,
):
    return entity_service.read_one(id_, db, token, request)
