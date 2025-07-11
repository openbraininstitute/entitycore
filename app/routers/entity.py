"""Entity router."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.db.types import EntityType
from app.dependencies.auth import UserContextDep
from app.dependencies.common import InBrainRegionDep
from app.dependencies.db import SessionDep
from app.schemas.entity import EntityCountRead
from app.service import entity as entity_service

router = APIRouter(
    prefix="/entity",
    tags=["entity"],
)


@router.get("/counts")
def count_entities_by_type(
    user_context: UserContextDep,
    db: SessionDep,
    types: Annotated[list[EntityType], Query(min_length=1, description="Entity types with count")],
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
