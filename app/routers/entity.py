"""Entity router."""

from typing import Annotated
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.db.model import Entity
from app.db.utils import EntityTypeWithBrainRegion
from app.dependencies.auth import AuthHeader, UserContextDep, check_user_info
from app.dependencies.common import InBrainRegionDep
from app.dependencies.db import SessionDep
from app.errors import (
    ensure_result,
)
from app.schemas.base import OptionalProjectContext
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
    with ensure_result(f"Entity {id_} not found or forbidden"):
        query = sa.select(Entity).where(Entity.id == id_)
        row = db.execute(query).unique().scalar_one()
        if row.authorized_public:
            return row

        user_context = token and check_user_info(
            OptionalProjectContext(project_id=row.authorized_project_id),
            token,
            request,
            find_vlab_id=True,
        )

        if user_context and user_context.is_authorized:
            entity = EntityRead.model_validate(row)
            entity.virtual_lab_id = user_context.virtual_lab_id
            return entity

    return None
