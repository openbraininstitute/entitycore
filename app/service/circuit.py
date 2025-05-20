import uuid

import sqlalchemy as sa

from app.db.model import Circuit
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.schemas.circuit import CircuitRead


def read_one(db: SessionDep, id_: uuid.UUID) -> CircuitRead:
    with ensure_result(error_message="Circuit not found"):
        stmt = sa.select(Circuit).filter(Circuit.id == id_)
        row = db.execute(stmt).scalar_one()
    return CircuitRead.model_validate(row)
