import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.model import Identifiable
from app.errors import (
    ensure_foreign_keys_integrity,
    ensure_result,
)


def get_identifiable_one[I: Identifiable](
    db: Session, db_model_class: type[I], id_: uuid.UUID
) -> I:
    """Get Identifiable resource from db."""
    query = sa.select(db_model_class).where(db_model_class.id == id_)
    with ensure_result(error_message=f"{db_model_class.__name__} not found"):
        obj = db.execute(query).scalars().one()

    return obj


def delete_one(db: Session, row) -> None:
    with ensure_foreign_keys_integrity(
        error_message=(
            f"{type(row).__name__} cannot be deleted because of foreign keys integrity violation"
        )
    ):
        # Use ORM delete in order to ensure that ondelete cascades are triggered in parents  when
        # subclasses are deleted as it is the case with Activity/SimulationGeneration.
        db.delete(row)
        db.flush()
