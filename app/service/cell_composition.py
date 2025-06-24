import uuid

import sqlalchemy as sa
from sqlalchemy.orm import (
    joinedload,
    raiseload,
    selectinload,
)

from app.db.model import (
    CellComposition,
    Contribution,
)
from app.dependencies.auth import UserContextDep
from app.dependencies.db import SessionDep
from app.queries.common import router_read_one
from app.schemas.cell_composition import (
    CellCompositionRead,
)


def _load(query: sa.Select):
    return query.options(
        joinedload(CellComposition.brain_region),
        joinedload(CellComposition.species, innerjoin=True),
        joinedload(CellComposition.created_by),
        joinedload(CellComposition.updated_by),
        selectinload(CellComposition.assets),
        selectinload(CellComposition.contributions).joinedload(Contribution.agent),
        selectinload(CellComposition.contributions).joinedload(Contribution.role),
        raiseload("*"),
    )


def read_one(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
) -> CellCompositionRead:
    return router_read_one(
        db=db,
        id_=id_,
        db_model_class=CellComposition,
        authorized_project_id=user_context.project_id,
        response_schema_class=CellCompositionRead,
        apply_operations=_load,
    )
