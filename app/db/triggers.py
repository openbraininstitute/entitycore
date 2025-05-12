from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute

from app.db.model import (
    Base,
    EModel,
    Entity,
    MEModel,
    NameDescriptionVectorMixin,
    ReconstructionMorphology,
)


def description_vector_trigger(
    model: type[DeclarativeBase], signature: str, target_field: str, fields: list[str]
):
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


def unauthorized_private_reference_function(
    model: type[Entity], field_name: str, target_model: type[Entity]
):
    table = model.__tablename__
    target = target_model.__tablename__
    signature = f"unauthorized_private_reference_function_{table}_{field_name}_{target}()"

    return PGFunction(
        "public",
        signature,
        f"""
            RETURNS TRIGGER AS $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM entity e1
                    JOIN entity e2 ON e2.id = NEW.id
                    WHERE e1.id = NEW.{field_name}
                    AND (e1.authorized_public = TRUE
                        OR (e2.authorized_public = FALSE
                            AND e1.authorized_project_id = e2.authorized_project_id
                        )
                    )
                ) THEN
                    RAISE EXCEPTION 'unauthorized private reference'
                        USING ERRCODE = '42501'; -- Insufficient Privilege
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """,  # noqa: S608
    )


def unauthorized_private_reference_trigger(
    model: type[Entity], field_name: str, target_model: type[Entity]
):
    table = model.__tablename__
    target = target_model.__tablename__
    signature = f"unauthorized_private_reference_trigger_{table}_{field_name}_{target}"
    function_ = f"unauthorized_private_reference_function_{table}_{field_name}_{target}"

    return PGTrigger(
        schema="public",
        signature=signature,
        on_entity=table,
        definition=f"""BEFORE INSERT OR UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION {function_}();
        """,
    )

entities = [
    description_vector_trigger(
        model=mapper.class_,
        signature=f"{mapper.class_.__tablename__}_description_vector",
        target_field="description_vector",
        fields=["description", "name"],
    )
    for mapper in Base.registry.mappers
    if issubclass(mapper.class_, NameDescriptionVectorMixin)
]

entities += [
    unauthorized_private_reference_function(
        EModel, "exemplar_morphology_id", ReconstructionMorphology
    ),
    unauthorized_private_reference_trigger(
        EModel, "exemplar_morphology_id", ReconstructionMorphology
    ),
    unauthorized_private_reference_function(MEModel, "morphology_id", ReconstructionMorphology),
    unauthorized_private_reference_trigger(MEModel, "morphology_id", ReconstructionMorphology),
    unauthorized_private_reference_function(MEModel, "emodel_id", EModel),
    unauthorized_private_reference_trigger(MEModel, "emodel_id", EModel),
]
