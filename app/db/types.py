from enum import StrEnum, auto, Enum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ARRAY, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column
from sqlalchemy.types import VARCHAR, TypeDecorator

from app.utils.enum import StrEnum


class PipelineType(StrEnum):
    Raw = auto()
    Curated = auto()
    Unraveled = auto()
    Repaired = auto()

class MorphologyType(StrEnum):
    DIGITAL = auto()
    MODIFIED = auto()
    COMPUTATIONAL = auto()
    PLACEHOLDER = auto()
    GENERIC = auto()

class MorphologyStructureType(str, Enum):
    digital_reconstruction = auto()
    modified = auto()
    computationally_synthesized = auto()
    placeholder = auto()
    generic = auto()  # for base CellMorphology


class PointLocationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    x: float
    y: float
    z: float


class PointLocationType(TypeDecorator):
    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: ARG002, PLR6301
        if value is None:
            return None

        if isinstance(value, dict):
            return value

        return value.model_dump()

    def process_result_value(self, value, dialect):  # noqa: ARG002, PLR6301
        if value is None:
            return None

        return PointLocationBase(**value)


PointLocation = Annotated[PointLocationType, "PointLocation"]

BIGINT = Annotated[int, mapped_column(BigInteger)]
JSON_DICT = Annotated[dict[str, Any], mapped_column(JSONB)]
STRING_LIST = Annotated[list[str], mapped_column(ARRAY(VARCHAR))]


class EntityType(StrEnum):
    """Entity types."""

    analysis_software_source_code = auto()
    brain_atlas = auto()
    brain_atlas_region = auto()
    cell_composition = auto()
    electrical_cell_recording = auto()
    electrical_recording_stimulus = auto()
    emodel = auto()
    experimental_bouton_density = auto()
    experimental_neuron_density = auto()
    experimental_synapses_per_connection = auto()
    ion_channel_model = auto()
    memodel = auto()
    mesh = auto()
    memodel_calibration_result = auto()
    me_type_density = auto()
    publication = auto()
    reconstruction_morphology = auto()
    simulation = auto()
    simulation_campaign = auto()
    simulation_campaign_generation = auto()
    simulation_execution = auto()
    simulation_result = auto()
    scientific_artifact = auto()
    single_neuron_simulation = auto()
    single_neuron_synaptome = auto()
    single_neuron_synaptome_simulation = auto()
    subject = auto()
    validation_result = auto()
    circuit = auto()


class AgentType(StrEnum):
    """Agent types."""

    person = auto()
    organization = auto()


class ActivityType(StrEnum):
    """Activity types."""

    simulation_execution = auto()
    simulation_generation = auto()


class DerivationType(StrEnum):
    """Represents the type of derivation relationship between two entities.

    Attributes:
        circuit_extraction: Indicates that the entity was derived by extracting a set of nodes from
         a circuit.
        circuit_rewiring: Indicates that the entity was derived by rewiring the connectivity of
          a circuit.
    """

    circuit_extraction = auto()
    circuit_rewiring = auto()


class AnnotationBodyType(StrEnum):
    """AnnotationBody types."""

    datamaturity_annotation_body = auto()


class AssetStatus(StrEnum):
    CREATED = auto()
    DELETED = auto()


class SingleNeuronSimulationStatus(StrEnum):
    started = auto()
    failure = auto()
    success = auto()


class SimulationExecutionStatus(StrEnum):
    created = auto()
    pending = auto()
    running = auto()
    done = auto()
    error = auto()


class ValidationStatus(StrEnum):
    created = auto()
    initialized = auto()
    running = auto()
    done = auto()
    error = auto()


class Sex(StrEnum):
    male = auto()
    female = auto()
    unknown = auto()


class ElectricalRecordingType(StrEnum):
    intracellular = auto()
    extracellular = auto()
    both = auto()
    unknown = auto()


class ElectricalRecordingStimulusType(StrEnum):
    voltage_clamp = auto()
    current_clamp = auto()
    conductance_clamp = auto()
    extracellular = auto()
    other = auto()
    unknown = auto()


class ElectricalRecordingStimulusShape(StrEnum):
    cheops = auto()
    constant = auto()
    pulse = auto()
    step = auto()
    ramp = auto()
    noise = auto()
    sinusoidal = auto()
    other = auto()
    two_steps = auto()
    unknown = auto()


class ElectricalRecordingOrigin(StrEnum):
    in_vivo = auto()
    in_vitro = auto()
    in_silico = auto()
    unknown = auto()


class AgePeriod(StrEnum):
    prenatal = auto()
    postnatal = auto()
    unknown = auto()


class MeasurementStatistic(StrEnum):
    mean = auto()
    median = auto()
    mode = auto()
    variance = auto()
    data_point = auto()
    sample_size = auto()
    standard_error = auto()
    standard_deviation = auto()
    raw = auto()
    minimum = auto()
    maximum = auto()
    sum = auto()


class MeasurementUnit(StrEnum):
    dimensionless = auto()
    linear_density__1_um = "1/μm"
    volume_density__1_mm3 = "1/mm³"
    linear__um = "μm"
    area__um2 = "μm²"
    volume__mm3 = "μm³"
    angle__radian = "radian"


class StructuralDomain(StrEnum):
    apical_dendrite = auto()
    basal_dendrite = auto()
    axon = auto()
    soma = auto()
    neuron_morphology = auto()


class ContentType(StrEnum):
    json = "application/json"
    swc = "application/swc"
    nrrd = "application/nrrd"
    obj = "application/obj"
    hoc = "application/hoc"
    asc = "application/asc"
    abf = "application/abf"
    nwb = "application/nwb"
    h5 = "application/x-hdf5"
    text = "text/plain"
    directory = "application/vnd.directory"
    mod = "application/mod"
    pdf = "application/pdf"
    png = "image/png"
    jpg = "image/jpeg"


class AssetLabel(StrEnum):
    """See docs/asset-labels.md."""

    morphology = auto()
    cell_composition_summary = auto()
    cell_composition_volumes = auto()
    single_neuron_synaptome_config = auto()
    single_neuron_synaptome_simulation_data = auto()
    single_cell_simulation_data = auto()
    sonata_circuit = auto()
    nwb = auto()
    neuron_hoc = auto()
    emodel_optimization_output = auto()
    sonata_simulation_config = auto()
    simulation_generation_config = auto()
    custom_node_sets = auto()
    campaign_generation_config = auto()
    campaign_summary = auto()
    replay_spikes = auto()
    voltage_report = auto()
    spike_report = auto()
    neuron_mechanisms = auto()
    brain_atlas_annotation = auto()
    brain_region_mesh = auto()
    voxel_densities = auto()
    validation_result_figure = auto()
    validation_result_details = auto()
    simulation_designer_image = auto()


class LabelRequirements(BaseModel):
    content_type: ContentType | None
    is_directory: bool


CONTENT_TYPE_TO_SUFFIX = {
    ContentType.json: (".json",),
    ContentType.swc: (".swc",),
    ContentType.nrrd: (".nrrd",),
    ContentType.obj: (".obj",),
    ContentType.hoc: (".hoc",),
    ContentType.asc: (".asc",),
    ContentType.abf: (".adf",),
    ContentType.nwb: (".nwb",),
    ContentType.h5: (".h5",),
    ContentType.text: (".txt",),
    ContentType.directory: (),
    ContentType.mod: (".mod",),
    ContentType.pdf: (".pdf",),
    ContentType.png: (".png",),
    ContentType.jpg: (
        ".jpg",
        ".jpeg",
    ),
}

ALLOWED_ASSET_LABELS_PER_ENTITY = {
    EntityType.brain_atlas: {
        AssetLabel.brain_atlas_annotation: [
            LabelRequirements(content_type=ContentType.nrrd, is_directory=False)
        ],
    },
    EntityType.brain_atlas_region: {
        AssetLabel.brain_region_mesh: [
            LabelRequirements(content_type=ContentType.obj, is_directory=False)
        ],
    },
    EntityType.cell_composition: {
        AssetLabel.cell_composition_summary: [
            LabelRequirements(content_type=ContentType.json, is_directory=False)
        ],
        AssetLabel.cell_composition_volumes: [
            LabelRequirements(content_type=ContentType.json, is_directory=False)
        ],
    },
    EntityType.circuit: {
        AssetLabel.sonata_circuit: [
            LabelRequirements(content_type=None, is_directory=True),
        ],
        AssetLabel.simulation_designer_image: [
            LabelRequirements(content_type=ContentType.png, is_directory=False)
        ],
    },
    EntityType.electrical_cell_recording: {
        AssetLabel.nwb: [
            LabelRequirements(content_type=ContentType.nwb, is_directory=False),
        ]
    },
    EntityType.emodel: {
        AssetLabel.emodel_optimization_output: [
            LabelRequirements(content_type=ContentType.json, is_directory=False)
        ],
        AssetLabel.neuron_hoc: [
            LabelRequirements(content_type=ContentType.hoc, is_directory=False)
        ],
    },
    EntityType.ion_channel_model: {
        AssetLabel.neuron_mechanisms: [
            LabelRequirements(content_type=ContentType.mod, is_directory=False)
        ],
    },
    EntityType.me_type_density: {
        AssetLabel.voxel_densities: [
            LabelRequirements(content_type=ContentType.nrrd, is_directory=False)
        ],
    },
    EntityType.reconstruction_morphology: {
        AssetLabel.morphology: [
            LabelRequirements(content_type=ContentType.asc, is_directory=False),
            LabelRequirements(content_type=ContentType.swc, is_directory=False),
            LabelRequirements(content_type=ContentType.h5, is_directory=False),
        ],
    },
    EntityType.simulation: {
        AssetLabel.custom_node_sets: [
            LabelRequirements(content_type=ContentType.json, is_directory=False)
        ],
        AssetLabel.replay_spikes: [
            LabelRequirements(content_type=ContentType.h5, is_directory=False)
        ],
        AssetLabel.simulation_generation_config: [
            LabelRequirements(content_type=ContentType.json, is_directory=False)
        ],
        AssetLabel.sonata_simulation_config: [
            LabelRequirements(content_type=ContentType.json, is_directory=False)
        ],
    },
    EntityType.simulation_campaign: {
        AssetLabel.campaign_generation_config: [
            LabelRequirements(content_type=ContentType.json, is_directory=False)
        ],
        AssetLabel.campaign_summary: [
            LabelRequirements(content_type=ContentType.json, is_directory=False)
        ],
    },
    EntityType.simulation_result: {
        AssetLabel.spike_report: [
            LabelRequirements(content_type=ContentType.h5, is_directory=False)
        ],
        AssetLabel.voltage_report: [
            LabelRequirements(content_type=ContentType.h5, is_directory=False),
            LabelRequirements(content_type=ContentType.nwb, is_directory=False),
        ],
    },
    EntityType.single_neuron_synaptome: {
        AssetLabel.single_neuron_synaptome_config: [
            LabelRequirements(content_type=ContentType.json, is_directory=False)
        ]
    },
    EntityType.single_neuron_synaptome_simulation: {
        AssetLabel.single_neuron_synaptome_simulation_data: [
            LabelRequirements(content_type=ContentType.json, is_directory=False)
        ]
    },
    EntityType.single_neuron_simulation: {
        AssetLabel.single_cell_simulation_data: [
            LabelRequirements(content_type=ContentType.json, is_directory=False)
        ]
    },
    EntityType.validation_result: {
        AssetLabel.validation_result_figure: [
            LabelRequirements(content_type=ContentType.pdf, is_directory=False),
            LabelRequirements(content_type=ContentType.png, is_directory=False),
        ],
        AssetLabel.validation_result_details: [
            LabelRequirements(content_type=ContentType.text, is_directory=False)
        ],
    },
}


class CircuitBuildCategory(StrEnum):
    """Information about how/from what source a circuit was built.

    - computational_model: Any type of data-driven or statistical model
    - em_reconstruction: Reconstruction from EM
    (More categories may be added later, if needed).
    """

    computational_model = auto()
    em_reconstruction = auto()


class CircuitScale(StrEnum):
    """Scale of the circuit.

    - single: Single neuron + extrinsic connectivity
    - pair: Two connected neurons + intrinsic connectivity + extrinsic connectivity
    - small: Small microcircuit (3-20 neurons) + intrinsic connectivity + extrinsic connectivity;
      usually containing specific connectivity motifs
    - microcircuit: Any circuit larger than 20 neurons but not being a region, system, or
      whole-brain circuit; may be atlas-based or not
    - region: Atlas-based continuous volume of an entire brain region or a set of continuous
      sub-regions
    - system: Non-continuous circuit consisting of at least two microcircuits/regions that are
      connected by inter-region connectivity
    - whole_brain: Circuit representing an entire brain.
    """

    single = auto()
    pair = auto()
    small = auto()
    microcircuit = auto()
    region = auto()
    system = auto()
    whole_brain = auto()
