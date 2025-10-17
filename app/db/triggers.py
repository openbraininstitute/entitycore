from alembic_utils.pg_extension import PGExtension
from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute

from app.db.model import (
    Base,
    CellMorphology,
    CellMorphologyProtocol,
    EModel,
    Entity,
    MEModel,
    NameDescriptionVectorMixin,
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
    model: type[Entity],
    field_name: str,
    target_model: type[Entity],
):
    """Return a PGFunction that checks that the model is not linked to unaccessible entities.

    A linked entity is considered accessible if and only if any of the following is true:

    - the new entity is private or public, and the linked entity is public.
    - the new entity is private, and the linked entity is in the same project.

    If the field is nullable and the value is NULL, then the check is skipped.

    A specific exception is raised if the linked entity is unaccessible.
    """
    table = model.__tablename__
    target = target_model.__tablename__
    signature = f"unauthorized_private_reference_function_{table}_{field_name}_{target}()"
    nullable = inspect(model).columns[field_name].nullable
    skip_if_null = f"IF NEW.{field_name} IS NULL THEN RETURN NEW; END IF;" if nullable else ""

    return PGFunction(
        "public",
        signature,
        f"""
            RETURNS TRIGGER AS $$
            BEGIN
                {skip_if_null}
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
    and "description_vector" in mapper.class_.__table__.c  # exclude children
]

entities += [
    PGExtension(schema="public", signature="vector"),
]

for model, field_name, target_model in [
    (EModel, "exemplar_morphology_id", CellMorphology),
    (MEModel, "morphology_id", CellMorphology),
    (MEModel, "emodel_id", EModel),
    (CellMorphology, "cell_morphology_protocol_id", CellMorphologyProtocol),
    # TODO: enable the following triggers for subject_id
    # (ScientificArtifact, "subject_id", Subject),
    # (ExperimentalNeuronDensity, "subject_id", Subject),
    # (ExperimentalBoutonDensity, "subject_id", Subject),
    # (ExperimentalSynapsesPerConnection, "subject_id", Subject),
]:
    entities += [
        unauthorized_private_reference_function(model, field_name, target_model),
        unauthorized_private_reference_trigger(model, field_name, target_model),
    ]


entities = []
