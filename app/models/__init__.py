from app.models.agent import Agent, Organization, Person
from app.models.annotation import (
    Annotation,
    DataMaturityAnnotationBody,
    ETypeAnnotationBody,
    MTypeAnnotationBody,
)
from app.models.base import (
    Base,
    BrainLocation,
    BrainRegion,
    License,
    Root,
    Species,
    Strain,
    Subject,
)
from app.models.entity import Entity
from app.models.contribution import Contribution
from app.models.density import (
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
)
from app.models.mesh import Mesh
from app.models.morphology import (
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
    ReconstructionMorphology,
)
from app.models.role import Role
from app.models.single_cell_experimental_trace import SingleCellExperimentalTrace
from app.models.memodel import MEModel
from app.models.code import AnalysisSoftwareSourceCode
from app.models.emodel import EModel
from app.models.single_neuron_synaptome import SingleNeuronSynaptome
from app.models.single_neuron_simulation import SingleNeuronSimulation

__all__ = [
    Role,
    SingleCellExperimentalTrace,
    MorphologyMeasurementSerieElement,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
    ReconstructionMorphology,
    Mesh,
    MorphologyFeatureAnnotation,
    Contribution,
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
    Agent,
    Organization,
    Person,
    Annotation,
    DataMaturityAnnotationBody,
    ETypeAnnotationBody,
    MTypeAnnotationBody,
    Base,
    BrainLocation,
    BrainRegion,
    Entity,
    License,
    Root,
    Species,
    Strain,
    Subject,
    MEModel,
    EModel,
    AnalysisSoftwareSourceCode,
    SingleNeuronSynaptome,
    SingleNeuronSimulation,
]


def init_db(uri):
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
