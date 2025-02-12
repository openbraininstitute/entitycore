# Schema

## Concepts


- **Entity**:

    Something that has a file associated with it

    Ex:

     - AnalysisSoftwareSourceCode
     - EModel
     - Mesh
     - MEModel
     - ReconstructionMorphology
     - SingleCellExperimentalTrace
     - SingleNeuronSynaptome
     - SingleNeuronSimulation
     - ExperimentalNeuronDensity
     - ExperimentalBoutonDensity
     - ExperimentalSynapsesPerConnection

- **Annotation**:
    An opinion about an entity.

    Different people may have different opinions of what qualifies the entity as having an `Annotation`.
    Thus, multiple `Annotation` may be applied to an Entity, within the same project.

    Ex:

     - MType for a ReconstructionMorphology
     - EType for a SingleCellExperimentalTrace

- **metadata**:

    data associated with an `Entity`

    This data can be changed at any point, so, for instance, the owner can decide that the BrainLocation was wrong, and change it.

    Ex:

     - Brain Location
     - Brain Region
     - License
     - Species
