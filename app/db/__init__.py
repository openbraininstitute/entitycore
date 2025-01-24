from app.db.model import (
    Agent,
    AnalysisSoftwareSourceCode,
    Annotation,
    Base,
    BrainLocation,
    BrainRegion,
    Contribution,
    DataMaturityAnnotationBody,
    EModel,
    ETypeAnnotationBody,
    Entity,
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
    License,
    MEModel,
    MTypeAnnotationBody,
    Mesh,
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
    Organization,
    Person,
    ReconstructionMorphology,
    Role,
    Root,
    SingleCellExperimentalTrace,
    SingleNeuronSimulation,
    SingleNeuronSynaptome,
    Species,
    Strain,
    Subject,
    StringList,
)

__all__ = [
    Agent,
    AnalysisSoftwareSourceCode,
    Annotation,
    Base,
    BrainLocation,
    BrainRegion,
    Contribution,
    DataMaturityAnnotationBody,
    EModel,
    ETypeAnnotationBody,
    Entity,
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
    License,
    MEModel,
    MTypeAnnotationBody,
    Mesh,
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
    Organization,
    Person,
    ReconstructionMorphology,
    Role,
    Root,
    SingleCellExperimentalTrace,
    SingleNeuronSimulation,
    SingleNeuronSynaptome,
    Species,
    Strain,
    Subject,
    StringList,
]


def init_db(uri):
    """create the database tables and triggers"""
    from sqlalchemy import create_engine, event
    from sqlalchemy.schema import DDL

    engine = create_engine(uri)
    Base.metadata.create_all(bind=engine)

    trigger_statement = DDL("""
    CREATE TRIGGER morphology_description_vector
        BEFORE INSERT OR UPDATE ON reconstruction_morphology
        FOR EACH ROW EXECUTE FUNCTION
            tsvector_update_trigger(morphology_description_vector, 'pg_catalog.english', description, name);
    """)
    # Associate the trigger with the table
    event.listen(
        ReconstructionMorphology.__table__,
        "after_create",
        trigger_statement,
    )


def get_db_sessionmaker(uri):
    """Get a sessionmaker"""
    from sqlalchemy import create_engine, sessionmaker

    engine = create_engine(uri)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
