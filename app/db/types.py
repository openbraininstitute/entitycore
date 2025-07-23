from enum import StrEnum, auto
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ARRAY, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column
from sqlalchemy.types import VARCHAR, TypeDecorator


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
    ion_channel_recording = auto()
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
    """Agent types.

    - person: Individual person
    - organization: Individual organization or institution
    - consortium: Group of individual persons (or organizations) formally joined together
    """

    person = auto()
    organization = auto()
    consortium = auto()


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


class IonChannel(StrEnum):
    kv1_1 = "Kv1.1"
    kv1_2 = "Kv1.2"
    kv1_3 = "Kv1.3"
    kv1_4 = "Kv1.4"
    kv1_5 = "Kv1.5"
    kv1_6 = "Kv1.6"
    kv1_7 = "Kv1.7"
    kv1_8 = "Kv1.8"
    kv2_1 = "Kv2.1"
    kv2_2 = "Kv2.2"
    kv3_1 = "Kv3.1"
    kv3_2 = "Kv3.2"
    kv3_3 = "Kv3.3"
    kv3_4 = "Kv3.4"
    kv4_1 = "Kv4.1"
    kv4_2 = "Kv4.2"
    kv4_3 = "Kv4.3"
    kv5_1 = "Kv5.1"
    kv6_1 = "Kv6.1"
    kv6_2 = "Kv6.2"
    kv6_3 = "Kv6.3"
    kv6_4 = "Kv6.4"
    kv7_1 = "Kv7.1"
    kv7_2 = "Kv7.2"
    kv7_3 = "Kv7.3"
    kv7_4 = "Kv7.4"
    kv7_5 = "Kv7.5"
    kv8_1 = "Kv8.1"
    kv8_2 = "Kv8.2"
    kv9_1 = "Kv9.1"
    kv9_2 = "Kv9.2"
    kv9_3 = "Kv9.3"
    kv10_1 = "Kv10.1"
    kv10_2 = "Kv10.2"
    kv11_1 = "Kv11.1"
    kv11_2 = "Kv11.2"
    kv11_3 = "Kv11.3"
    kv12_1 = "Kv12.1"
    kv12_2 = "Kv12.2"
    kv12_3 = "Kv12.3"
    kir1_1 = "Kir1.1"
    kir2_1 = "Kir2.1"
    kir2_2 = "Kir2.2"
    kir2_3 = "Kir2.3"
    kir2_4 = "Kir2.4"
    kir3_1 = "Kir3.1"
    kir3_2 = "Kir3.2"
    kir3_3 = "Kir3.3"
    kir3_4 = "Kir3.4"
    kir4_1 = "Kir4.1"
    kir4_2 = "Kir4.2"
    kir5_1 = "Kir5.1"
    kir6_1 = "Kir6.1"
    kir6_2 = "Kir6.2"
    kir7_1 = "Kir7.1"
    sk1 = "SK1"
    sk2 = "SK2"
    sk3 = "SK3"
    sk4 = "SK4"
    slo1 = "Slo1"
    slo2 = "Slo2"
    slo2b = "Slo2b"
    slo3 = "Slo3"
    talk1 = "TALK1"
    talk2 = "TALK2"
    task1 = "TASK1"
    task2 = "TASK2"
    task3 = "TASK3"
    task5 = "TASK5"
    thik1 = "THIK1"
    thik2 = "THIK2"
    traak = "TRAAK"
    trek1 = "TREK1"
    trek2 = "TREK2"
    tresk2 = "TRESK2"
    twik1 = "TWIK1"
    twik2 = "TWIK2"
    twik3 = "TWIK3"
    nav1_1 = "Nav1.1"
    nav1_2 = "Nav1.2"
    nav1_3 = "Nav1.3"
    nav1_4 = "Nav1.4"
    nav1_5 = "Nav1.5"
    nav1_6 = "Nav1.6"
    nav1_7 = "Nav1.7"
    nav1_8 = "Nav1.8"
    nav1_9 = "Nav1.9"
    nag = "NaG"
    cav1_1 = "Cav1.1"
    cav1_2 = "Cav1.2"
    cav1_3 = "Cav1.3"
    cav1_4 = "Cav1.4"
    cav2_1 = "Cav2.1"
    cav2_2 = "Cav2.2"
    cav2_3 = "Cav2.3"
    cav3_1 = "Cav3.1"
    cav3_2 = "Cav3.2"
    cav3_3 = "Cav3.3"
    clc1 = "ClC1"
    clc2 = "ClC2"
    clc3 = "ClC3"
    clc4 = "ClC4"
    clc5 = "ClC5"
    clc6 = "ClC6"
    clc7 = "ClC7"
    clck1 = "ClCK1"
    clck2 = "ClCK2"
    clic1 = "ClIC1"
    clic2 = "ClIC2"
    clic3 = "ClIC3"
    clic4 = "ClIC4"
    clic5 = "ClIC5"
    hcn1 = "HCN1"
    hcn2 = "HCN2"
    hcn3 = "HCN3"
    hcn4 = "HCN4"
    hlc5 = "HLC5"
    trpa1 = "TRPA1"
    trpc1 = "TRPC1"
    trpc2 = "TRPC2"
    trpc3 = "TRPC3"
    trpc4 = "TRPC4"
    trpc5 = "TRPC5"
    trpc6 = "TRPC6"
    trpc7 = "TRPC7"
    trpm1 = "TRPM1"
    trpm2 = "TRPM2"
    trpm3 = "TRPM3"
    trpm4 = "TRPM4"
    trpm5 = "TRPM5"
    trpm6 = "TRPM6"
    trpm7 = "TRPM7"
    trpm8 = "TRPM8"
    trpml1 = "TRPML1"
    trpml2 = "TRPML2"
    trpml3 = "TRPML3"
    trpp1 = "TRPP1"
    trpp2 = "TRPP2"
    trpp3 = "TRPP3"
    trpv1 = "TRPV1"
    trpv2 = "TRPV2"
    trpv3 = "TRPV3"
    trpv4 = "TRPV4"
    trpv5 = "TRPV5"
    trpv6 = "TRPV6"


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
    gltf_binary = "model/gltf-binary"
    gzip = "application/gzip"
    webp = "image/webp"


class AssetLabel(StrEnum):
    """See docs/asset-labels.md."""

    morphology = auto()
    cell_composition_summary = auto()
    cell_composition_volumes = auto()
    single_neuron_synaptome_config = auto()
    single_neuron_synaptome_simulation_data = auto()
    single_neuron_simulation_data = auto()
    sonata_circuit = auto()
    compressed_sonata_circuit = auto()
    circuit_figures = auto()
    circuit_analysis_data = auto()
    circuit_connectivity_matrices = auto()
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
    brain_atlas_region_mesh = auto()
    voxel_densities = auto()
    validation_result_figure = auto()
    validation_result_details = auto()
    simulation_designer_image = auto()
    circuit_visualization = auto()
    node_stats = auto()
    network_stats_A = auto()
    network_stats_B = auto()


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
    ContentType.gltf_binary: (".glb",),
    ContentType.gzip: (
        ".gz",
        ".gzip",
        ".tgz",
    ),
    ContentType.webp: (".webp",),
}

ALLOWED_ASSET_LABELS_PER_ENTITY = {
    EntityType.brain_atlas: {
        AssetLabel.brain_atlas_annotation: [
            LabelRequirements(content_type=ContentType.nrrd, is_directory=False)
        ],
    },
    EntityType.brain_atlas_region: {
        AssetLabel.brain_atlas_region_mesh: [
            LabelRequirements(content_type=ContentType.obj, is_directory=False),
            LabelRequirements(content_type=ContentType.gltf_binary, is_directory=False),
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
        AssetLabel.compressed_sonata_circuit: [
            LabelRequirements(content_type=ContentType.gzip, is_directory=False),
        ],
        AssetLabel.circuit_figures: [
            LabelRequirements(content_type=None, is_directory=True),
        ],
        AssetLabel.circuit_analysis_data: [
            LabelRequirements(content_type=None, is_directory=True),
        ],
        AssetLabel.circuit_connectivity_matrices: [
            LabelRequirements(content_type=None, is_directory=True),
        ],
        AssetLabel.simulation_designer_image: [
            LabelRequirements(content_type=ContentType.png, is_directory=False)
        ],
        AssetLabel.circuit_visualization: [
            LabelRequirements(content_type=ContentType.webp, is_directory=False)
        ],
        AssetLabel.node_stats: [
            LabelRequirements(content_type=ContentType.webp, is_directory=False)
        ],
        AssetLabel.network_stats_A: [
            LabelRequirements(content_type=ContentType.webp, is_directory=False)
        ],
        AssetLabel.network_stats_B: [
            LabelRequirements(content_type=ContentType.webp, is_directory=False)
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
        AssetLabel.single_neuron_simulation_data: [
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
