import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.orm import joinedload, raiseload

from app.db.auth import constrain_to_accessible_entities
from app.db.model import (
    Entity,
    ETypeClassification,
)
from app.dependencies.auth import UserContextWithProjectIdDep
from app.dependencies.db import SessionDep
from app.logger import L
from app.queries.common import router_create_one
from app.schemas.classification import (
    ETypeClassificationCreate,
    ETypeClassificationRead,
)


def _load(query: sa.Select):
    return query.options(
        joinedload(ETypeClassification.created_by),
        joinedload(ETypeClassification.updated_by),
        raiseload("*"),
    )


def create_one(
    db: SessionDep,
    json_model: ETypeClassificationCreate,
    user_context: UserContextWithProjectIdDep,
) -> ETypeClassificationRead:
    stmt = constrain_to_accessible_entities(
        sa.select(sa.func.count(Entity.id)).where(Entity.id == json_model.entity_id),
        user_context.project_id,
    )
    if db.execute(stmt).scalar_one() == 0:
        L.warning("Attempting to create an annotation for an entity inaccessible to user")
        raise HTTPException(status_code=404, detail=f"Cannot access entity {json_model.entity_id}")

    if not json_model.authorized_public:
        L.warning("Attempting to create a private classification, which is not supported.")
        raise HTTPException(
            status_code=404,
            detail="Private classifications are not supported. Use authorized_public=True",
        )
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=ETypeClassification,
        response_schema_class=ETypeClassificationRead,
        apply_operations=_load,
    )
