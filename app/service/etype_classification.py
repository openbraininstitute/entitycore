import sqlalchemy as sa
from sqlalchemy.orm import joinedload, raiseload

from app.db.model import (
    ETypeClassification,
)
from app.dependencies.auth import UserContextWithProjectIdDep
from app.dependencies.db import SessionDep
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
    return router_create_one(
        db=db,
        json_model=json_model,
        user_context=user_context,
        db_model_class=ETypeClassification,
        response_schema_class=ETypeClassificationRead,
        apply_operations=_load,
    )
