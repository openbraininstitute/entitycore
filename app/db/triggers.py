from alembic_utils.pg_trigger import PGTrigger

from app.db.model import ReconstructionMorphology

entities = [
    PGTrigger(
        schema="public",
        signature="morphology_description_vector",
        on_entity=ReconstructionMorphology.__tablename__,
        definition=f"""
            BEFORE INSERT OR UPDATE ON {ReconstructionMorphology.__tablename__}
            FOR EACH ROW EXECUTE FUNCTION
                tsvector_update_trigger(morphology_description_vector, 'pg_catalog.english', description, name)
        """,  # noqa: E501
    )
]
