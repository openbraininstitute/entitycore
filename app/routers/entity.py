"""Entity router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.db.model import Entity
from app.db.utils import EntityTypeWithBrainRegion
from app.dependencies.auth import UserContextDep
from app.dependencies.common import InBrainRegionDep
from app.dependencies.db import SessionDep
from app.queries.entity import get_readable_entity
from app.schemas.entity import EntityCountRead
from app.service import entity as entity_service

router = APIRouter(
    prefix="/entity",
    tags=["entity"],
)


@router.get("/{id_}")
def read_one(
    id_: UUID,
    db: SessionDep,
    user_context: UserContextDep,
):
    return get_readable_entity(
        db=db,
        db_model_class=Entity,
        entity_id=id_,
        project_id=user_context.project_id,
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
