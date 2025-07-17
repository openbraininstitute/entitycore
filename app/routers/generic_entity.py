"""Entity router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from app.dependencies.auth import verify_token

from app.db.model import Entity
from app.db.utils import EntityTypeWithBrainRegion
from app.dependencies.auth import UserContextDep
from app.dependencies.common import InBrainRegionDep
from app.dependencies.db import SessionDep
from app.queries.entity import get_readable_entity
from app.schemas.entity import EntityCountRead, EntityRead
from app.service import entity as entity_service

from app.errors import (
    ensure_authorized_references,
    ensure_foreign_keys_integrity,
    ensure_result,
    ensure_uniqueness,
)
import sqlalchemy as sa

router = APIRouter(
    prefix="/generic-entity",
    tags=["entity"],
)

from app.logger import L


@router.get("/{id_}", response_model=EntityRead)
def read_one(id_: UUID, db: SessionDep):
    L.info("\n\n\n here called")

    with ensure_result(f"Entity {id_} not found or forbidden"):
        query = sa.select(Entity).where(Entity.id == id_)
        row = db.execute(query).unique().scalar_one()
        if row.authorized_public:
            return row

    return None
