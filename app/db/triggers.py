import hashlib

from alembic_utils.pg_extension import PGExtension
from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute

from app.db.model import (
    Base,
    BrainAtlasRegion,
    CellMorphology,
    Circuit,
    CircuitExtractionConfig,
    ElectricalRecordingStimulus,
    EMCellMesh,
    EModel,
    Entity,
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
    IonChannelModelingConfig,
    MEModel,
    MEModelCalibrationResult,
    NameDescriptionVectorMixin,
    ScientificArtifact,
    Simulation,
    SimulationCampaign,
    SimulationResult,
    SingleNeuronSimulation,
    SingleNeuronSynaptome,
    SingleNeuronSynaptomeSimulation,
    SkeletonizationConfig,
    ValidationResult,
)

MAX_IDENTIFIER_LENGTH = 59


def _check_name_length(s: str, min_len: int = 1, max_len: int = 63) -> str:
    """Check that the length isn't greater than the maximum identifier length in PostgreSQL.

    If longer names are written in commands, they are truncated.

    See: https://www.postgresql.org/docs/current/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS
    """
    if len(s) < min_len:
        msg = f"Minimum identifier length is {min_len} bytes, but {s!r} is {len(s)}"
        raise ValueError(msg)
    if len(s) > max_len:
        msg = f"Maximum identifier length is {max_len} bytes, but {s!r} is {len(s)}"
        raise ValueError(msg)
    return s


def _truncate_identifier(name: str) -> str:
    if len(name) <= MAX_IDENTIFIER_LENGTH:
        return name

    checksum = hashlib.sha1(name.encode()).hexdigest()[:8]  # noqa: S324

    max_length = MAX_IDENTIFIER_LENGTH
    truncated = name[: max_length - 9]

    final_name = f"{truncated}_{checksum}"

    return final_name


def _get_unauthorized_function_name(table: str, field_name: str) -> str:
    name = _truncate_identifier(f"auth_fnc_{table}_{field_name}")
    return _check_name_length(name)


def _get_unauthorized_trigger_name(table: str, field_name: str) -> str:
    name = _truncate_identifier(f"auth_trg_{table}_{field_name}")
    return _check_name_length(name)


def description_vector_trigger(
    model: type[DeclarativeBase], signature: str, target_field: str, fields: list[str]
):
    if not fields:
        msg = "At least one field required"
        raise TypeError(msg)

    for field in [target_field, *fields]:
        if not isinstance(getattr(model, field, None), InstrumentedAttribute):
            msg = f"{field!r} is not a column of {model.__name__}"
            raise TypeError(msg)

    return PGTrigger(
        schema="public",
        signature=_check_name_length(signature),
        on_entity=model.__tablename__,
        definition=f"""
            BEFORE INSERT OR UPDATE ON {model.__tablename__}
            FOR EACH ROW EXECUTE FUNCTION
                tsvector_update_trigger({target_field}, 'pg_catalog.english', {", ".join(fields)})
        """,
    )


def unauthorized_private_reference_function(model: type[Entity], field_name: str) -> PGFunction:
    """Return a PGFunction that checks that the model is not linked to unaccessible entities.

    A linked entity is considered accessible if and only if any of the following is true:

    - the new entity is private or public, and the linked entity is public.
    - the new entity is private, and the linked entity is in the same project.

    If the field is nullable and the value is NULL, then the check is skipped.

    A specific exception is raised if the linked entity is unaccessible.
    """
    table = model.__tablename__
    function_name = _get_unauthorized_function_name(table, field_name)
    nullable = inspect(model).columns[field_name].nullable
    skip_if_null = f"IF NEW.{field_name} IS NULL THEN RETURN NEW; END IF;" if nullable else ""

    return PGFunction(
        schema="public",
        signature=f"{function_name}()",
        definition=f"""
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
                    RAISE EXCEPTION 'unauthorized private reference: {table}.{field_name}'
                        USING ERRCODE = '42501'; -- Insufficient Privilege
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """,  # noqa: S608
    )


def unauthorized_private_reference_trigger(model: type[Entity], field_name: str) -> PGTrigger:
    table = model.__tablename__
    trigger_name = _get_unauthorized_trigger_name(table, field_name)
    function_name = _get_unauthorized_function_name(table, field_name)

    return PGTrigger(
        schema="public",
        signature=trigger_name,
        on_entity=table,
        definition=f"""BEFORE INSERT OR UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION {function_name}();
        """,
    )


# list of protected relationships between entities as (model, field_name)
protected_entity_relationships = [
    (BrainAtlasRegion, "brain_atlas_id"),
    (CellMorphology, "cell_morphology_protocol_id"),
    (Circuit, "atlas_id"),
    (Circuit, "root_circuit_id"),
    (CircuitExtractionConfig, "circuit_id"),
    (ElectricalRecordingStimulus, "recording_id"),
    (EMCellMesh, "em_dense_reconstruction_dataset_id"),
    (EModel, "exemplar_morphology_id"),
    (ExperimentalBoutonDensity, "subject_id"),
    (ExperimentalNeuronDensity, "subject_id"),
    (ExperimentalSynapsesPerConnection, "subject_id"),
    (MEModel, "emodel_id"),
    (MEModel, "morphology_id"),
    (MEModelCalibrationResult, "calibrated_entity_id"),
    (ScientificArtifact, "subject_id"),
    (Simulation, "entity_id"),
    (Simulation, "simulation_campaign_id"),
    (SimulationCampaign, "entity_id"),
    (SimulationResult, "simulation_id"),
    (SingleNeuronSimulation, "me_model_id"),
    (SingleNeuronSynaptome, "me_model_id"),
    (SingleNeuronSynaptomeSimulation, "synaptome_id"),
    (ValidationResult, "validated_entity_id"),
    (IonChannelModelingConfig, "ion_channel_modeling_campaign_id"),
    (SkeletonizationConfig, "skeletonization_campaign_id"),
    (SkeletonizationConfig, "em_cell_mesh_id"),
]

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

for model, field_name in protected_entity_relationships:
    entities += [
        unauthorized_private_reference_function(model, field_name),
        unauthorized_private_reference_trigger(model, field_name),
    ]
