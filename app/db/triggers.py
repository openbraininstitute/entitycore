from typing import TypeVar

from alembic_utils.pg_trigger import PGTrigger
from sqlalchemy.orm import DeclarativeMeta, InstrumentedAttribute

from app.db.model import EModel, ReconstructionMorphology

M = TypeVar("M", bound=DeclarativeMeta)


def description_vector_trigger(model: M, signature: str, target_field: str, fields: list[str]):  # noqa: UP047
    if not fields:
        msg = "At least one field required"
        raise TypeError(msg)

    for field in [target_field, *fields]:
        if not isinstance(getattr(model, field), InstrumentedAttribute):
            msg = f"{field} is not a column of {model}"
            raise TypeError(msg)

    return PGTrigger(
        schema="public",
        signature=signature,
        on_entity=model.__tablename__,
        definition=f"""
            BEFORE INSERT OR UPDATE ON {model.__tablename__}
            FOR EACH ROW EXECUTE FUNCTION
                tsvector_update_trigger({target_field}, 'pg_catalog.english', {", ".join(fields)})
        """,
    )


entities = [
    description_vector_trigger(
        ReconstructionMorphology,
        "morphology_description_vector",
        "morphology_description_vector",
        ["description", "name"],
    ),
    description_vector_trigger(
        EModel,
        "emodel_description_vector",
        "description_vector",
        ["description", "name"],
    ),
]
