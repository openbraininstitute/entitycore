from app.db.model import (
    EModel,
    Entity,
    ExperimentalBoutonDensity,
    ExperimentalNeuronDensity,
    ExperimentalSynapsesPerConnection,
    Mesh,
    ReconstructionMorphology,
    SingleCellExperimentalTrace,
)
from app.db.types import EntityType

ENTITY_TYPE_TO_CLASS: dict[EntityType, type[Entity]] = {
    EntityType.emodel: EModel,
    EntityType.experimental_bouton_density: ExperimentalBoutonDensity,
    EntityType.experimental_neuron_density: ExperimentalNeuronDensity,
    EntityType.experimental_synapses_per_connection: ExperimentalSynapsesPerConnection,
    EntityType.mesh: Mesh,
    EntityType.reconstruction_morphology: ReconstructionMorphology,
    EntityType.single_cell_experimental_trace: SingleCellExperimentalTrace,
}
