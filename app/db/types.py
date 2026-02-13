from enum import StrEnum, auto
from typing import Annotated, Any, TypedDict

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ARRAY, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column
from sqlalchemy.types import VARCHAR, TypeDecorator

from app.utils.enum import combine_str_enums


class RepairPipelineType(StrEnum):
    raw = auto()
    curated = auto()
    unraveled = auto()
    repaired = auto()


class ModifiedMorphologyMethodType(StrEnum):
    cloned = auto()
    mix_and_match = auto()
    mousified = auto()
    ratified = auto()


class CellMorphologyGenerationType(StrEnum):
    digital_reconstruction = auto()
    modified_reconstruction = auto()
    computationally_synthesized = auto()
    placeholder = auto()


class CellMorphologyProtocolDesign(StrEnum):
    electron_microscopy = auto()
    cell_patch = auto()
    fluorophore = auto()
    topological_synthesis = auto()


class SlicingDirectionType(StrEnum):
    coronal = auto()
    sagittal = auto()
    horizontal = auto()
    custom = auto()


class StainingType(StrEnum):
    golgi = auto()
    nissl = auto()
    luxol_fast_blue = auto()
    fluorescent_nissl = auto()
    fluorescent_dyes = auto()
    fluorescent_protein_expression = auto()
    immunohistochemistry = auto()
    other = auto()


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


class StorageType(StrEnum):
    """Storage type."""

    aws_s3_internal = auto()
    aws_s3_open = auto()


class EntityType(StrEnum):
    """Entity types."""

    analysis_software_source_code = auto()
    brain_atlas = auto()
    brain_atlas_region = auto()
    cell_composition = auto()
    cell_morphology = auto()
    cell_morphology_protocol = auto()
    electrical_cell_recording = auto()
    electrical_recording = auto()
    electrical_recording_stimulus = auto()
    emodel = auto()
    experimental_bouton_density = auto()
    experimental_neuron_density = auto()
    experimental_synapses_per_connection = auto()
    external_url = auto()
    ion_channel_model = auto()
    ion_channel_modeling_campaign = auto()
    ion_channel_modeling_config = auto()
    ion_channel_recording = auto()
    memodel = auto()
    memodel_calibration_result = auto()
    me_type_density = auto()
    simulation = auto()
    simulation_campaign = auto()
    simulation_result = auto()
    scientific_artifact = auto()
    single_neuron_simulation = auto()
    single_neuron_synaptome = auto()
    single_neuron_synaptome_simulation = auto()
    subject = auto()
    validation_result = auto()
    circuit = auto()
    circuit_extraction_campaign = auto()
    circuit_extraction_config = auto()
    em_dense_reconstruction_dataset = auto()
    em_cell_mesh = auto()
    analysis_notebook_template = auto()
    analysis_notebook_environment = auto()
    analysis_notebook_result = auto()
    skeletonization_config = auto()
    skeletonization_campaign = auto()
    campaign = auto()
    item_config = auto()


class TaskType(StrEnum):
    """Task types for campaigns."""

    circuit_simulation = auto()
    circuit_extraction = auto()
    ion_channel_modeling = auto()
    skeletonization = auto()
    ion_channel_simulation = auto()
    em_synapse_mapping = auto()


class AgentType(StrEnum):
    """Agent types.

    - person: Individual person
    - organization: Individual organization or institution
    - consortium: Group of individual persons (or organizations) formally joined together
    """

    person = auto()
    organization = auto()
    consortium = auto()


class GlobalType(StrEnum):
    """Global resource types."""

    brain_region_hierarchy = auto()
    brain_region = auto()
    species = auto()
    strain = auto()
    license = auto()
    mtype_class = auto()
    etype_class = auto()
    publication = auto()
    role = auto()
    ion = auto()
    ion_channel = auto()
    measurement_annotation = auto()
    measurement_label = auto()


class AssociationType(StrEnum):
    etype_classification = auto()
    mtype_classification = auto()
    contribution = auto()
    derivation = auto()
    scientific_artifact_publication_link = auto()
    scientific_artifact_external_url_link = auto()


class ActivityType(StrEnum):
    """Activity types."""

    simulation_execution = auto()
    simulation_generation = auto()
    validation = auto()
    calibration = auto()
    analysis_notebook_execution = auto()
    ion_channel_modeling_execution = auto()
    ion_channel_modeling_config_generation = auto()
    circuit_extraction_config_generation = auto()
    circuit_extraction_execution = auto()
    skeletonization_execution = auto()
    skeletonization_config_generation = auto()
    config_generation = auto()
    config_execution = auto()


class DerivationType(StrEnum):
    """Represents the type of derivation relationship between two entities.

    Attributes:
        circuit_extraction: Indicates that the entity was derived by extracting a set of nodes from
         a circuit.
        circuit_rewiring: Indicates that the entity was derived by rewiring the connectivity of
          a circuit.
        unspecified: Indicates a derivation that does not require a specific type.
    """

    circuit_extraction = auto()
    circuit_rewiring = auto()
    unspecified = auto()


ResourceType = combine_str_enums(
    "ResourceType",
    (EntityType, AssociationType, GlobalType, AgentType, ActivityType),
)


class AnnotationBodyType(StrEnum):
    """AnnotationBody types."""

    datamaturity_annotation_body = auto()


class AssetStatus(StrEnum):
    CREATED = auto()
    UPLOADING = auto()
    DELETED = auto()


class ValidationStatus(StrEnum):
    # TODO: To be removed once validation_status is removed
    created = auto()
    initialized = auto()
    running = auto()
    done = auto()
    error = auto()


class ActivityStatus(StrEnum):
    created = auto()
    pending = auto()
    running = auto()
    done = auto()
    error = auto()
    cancelled = auto()


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
    area_density__1_um2 = "1/μm²"
    volume_density__1_mm3 = "1/mm³"
    linear__um = "μm"
    area__um2 = "μm²"
    volume__um3 = "μm³"
    angle__radian = "radian"


class StructuralDomain(StrEnum):
    apical_dendrite = auto()
    basal_dendrite = auto()
    axon = auto()
    soma = auto()
    neuron_morphology = auto()
    not_applicable = auto()


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
    ipynb = "application/x-ipynb+json"
    zip = "application/zip"


class AssetLabel(StrEnum):
    """See docs/asset-labels.md."""

    morphology = auto()
    morphology_with_spines = auto()
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
    ion_channel_modeling_generation_config = auto()
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
    network_stats_a = auto()
    network_stats_b = auto()
    cell_surface_mesh = auto()
    jupyter_notebook = auto()
    requirements = auto()
    notebook_required_files = auto()
    ion_channel_model_figure = auto()
    ion_channel_model_figure_summary_json = auto()
    ion_channel_model_thumbnail = auto()
    circuit_extraction_config = auto()
    skeletonization_config = auto()


class LabelRequirements(BaseModel):
    content_type: ContentType | None
    is_directory: bool
    description: str = ""


CONTENT_TYPE_TO_SUFFIX: dict[ContentType, tuple[str, ...]] = {
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
    ContentType.ipynb: (".ipynb",),
    ContentType.zip: (".zip",),
}

ALLOWED_ASSET_LABELS_PER_ENTITY: dict[
    EntityType, dict[AssetLabel, list[LabelRequirements]] | None
] = {
    EntityType.analysis_notebook_template: {
        AssetLabel.jupyter_notebook: [
            LabelRequirements(
                content_type=ContentType.ipynb,
                is_directory=False,
                description="Jupyter notebook file.",
            )
        ],
        AssetLabel.notebook_required_files: [
            LabelRequirements(
                content_type=ContentType.zip,
                is_directory=False,
                description=(
                    "Optional archive for additional required files not available as entities."
                ),
            )
        ],
        AssetLabel.requirements: [
            LabelRequirements(
                content_type=ContentType.text,
                is_directory=False,
                description=(
                    "File `requirements.txt` containing the required packages, frozen if possible."
                ),
            )
        ],
    },
    EntityType.analysis_notebook_environment: {
        AssetLabel.requirements: [
            LabelRequirements(
                content_type=ContentType.text,
                is_directory=False,
                description="File `requirements.txt` containing the frozen packages.",
            )
        ],
    },
    EntityType.analysis_notebook_result: {
        AssetLabel.jupyter_notebook: [
            LabelRequirements(
                content_type=ContentType.ipynb,
                is_directory=False,
                description="Jupyter notebook file.",
            )
        ],
        AssetLabel.notebook_required_files: [
            LabelRequirements(
                content_type=ContentType.zip,
                is_directory=False,
                description=(
                    "Optional archive for additional required files not available as entities."
                ),
            )
        ],
    },
    EntityType.brain_atlas: {
        AssetLabel.brain_atlas_annotation: [
            LabelRequirements(
                content_type=ContentType.nrrd,
                is_directory=False,
                description="Brain atlas annotation nrrd volume.",
            )
        ],
    },
    EntityType.brain_atlas_region: {
        AssetLabel.brain_atlas_region_mesh: [
            LabelRequirements(
                content_type=ContentType.obj,
                is_directory=False,
                description="Brain atlas region mesh geometry object.",
            ),
            LabelRequirements(
                content_type=ContentType.gltf_binary,
                is_directory=False,
                description="Brain atlas region mesh binary geometry object.",
            ),
        ],
    },
    EntityType.cell_composition: {
        AssetLabel.cell_composition_summary: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Region/mtype/etype densities summary.",
            )
        ],
        AssetLabel.cell_composition_volumes: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Mtype/etype voxel densities composition.",
            )
        ],
    },
    EntityType.circuit: {
        AssetLabel.sonata_circuit: [
            LabelRequirements(
                content_type=None,
                is_directory=True,
                description=(
                    "SONATA circuit, with a circuit_config.json in the root of the directory."
                ),
            ),
        ],
        AssetLabel.compressed_sonata_circuit: [
            LabelRequirements(
                content_type=ContentType.gzip,
                is_directory=False,
                description="Compressed SONATA circuit in tarred gzip format.",
            ),
        ],
        AssetLabel.circuit_figures: [
            LabelRequirements(
                content_type=None,
                is_directory=True,
                description=(
                    "Circuit figures with a figure_config.json in the root of the directory."
                ),
            ),
        ],
        AssetLabel.circuit_analysis_data: [
            LabelRequirements(
                content_type=None,
                is_directory=True,
                description=(
                    "Circuit analysis data with an analysis_config.json "
                    "in the root of the directory."
                ),
            ),
        ],
        AssetLabel.circuit_connectivity_matrices: [
            LabelRequirements(
                content_type=None,
                is_directory=True,
                description=(
                    "Connectivity matrices in ConnectomeUtilities format, "
                    "with a matrix_config.json in the root of the directory."
                ),
            ),
        ],
        AssetLabel.simulation_designer_image: [
            LabelRequirements(
                content_type=ContentType.png,
                is_directory=False,
                description="Circuit image used by simulation designer GUI.",
            )
        ],
        AssetLabel.circuit_visualization: [
            LabelRequirements(
                content_type=ContentType.webp,
                is_directory=False,
                description="Circuit visualization image.",
            )
        ],
        AssetLabel.node_stats: [
            LabelRequirements(
                content_type=ContentType.webp,
                is_directory=False,
                description="Circuit node statistics image.",
            )
        ],
        AssetLabel.network_stats_a: [
            LabelRequirements(
                content_type=ContentType.webp,
                is_directory=False,
                description=(
                    "Circuit network statistics image A "
                    "with global network statistics or visualizations."
                ),
            )
        ],
        AssetLabel.network_stats_b: [
            LabelRequirements(
                content_type=ContentType.webp,
                is_directory=False,
                description=(
                    "Circuit network statistics image B with pathway statistics or visualizations."
                ),
            )
        ],
    },
    EntityType.electrical_cell_recording: {
        AssetLabel.nwb: [
            LabelRequirements(
                content_type=ContentType.nwb,
                is_directory=False,
                description="Electrophysiological timeseries data.",
            ),
        ]
    },
    EntityType.emodel: {
        AssetLabel.emodel_optimization_output: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description=(
                    "Electrical model optimized parameters, and electrical feature: "
                    "values and scores."
                ),
            )
        ],
        AssetLabel.neuron_hoc: [
            LabelRequirements(
                content_type=ContentType.hoc,
                is_directory=False,
                description="Electrical model NEURON template.",
            )
        ],
    },
    EntityType.ion_channel_model: {
        AssetLabel.neuron_mechanisms: [
            LabelRequirements(
                content_type=ContentType.mod,
                is_directory=False,
                description="Ionic mechanisms file.",
            )
        ],
        AssetLabel.ion_channel_model_figure: [
            LabelRequirements(
                content_type=ContentType.pdf,
                is_directory=False,
                description="Ionic mechanism activation protocol responses.",
            )
        ],
        AssetLabel.ion_channel_model_thumbnail: [
            LabelRequirements(
                content_type=ContentType.png,
                is_directory=False,
                description="Thumbnail showing activation protocol responses.",
            )
        ],
        AssetLabel.ion_channel_model_figure_summary_json: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Figure summary for page ordering.",
            )
        ],
    },
    EntityType.ion_channel_modeling_config: {
        AssetLabel.ion_channel_modeling_generation_config: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Obi-One model generation workflow configuration.",
            )
        ],
    },
    EntityType.ion_channel_modeling_campaign: {
        AssetLabel.campaign_generation_config: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Obi-One modeling campaign configuration.",
            )
        ],
        AssetLabel.campaign_summary: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Obi-One modeling campaign summary.",
            )
        ],
    },
    EntityType.ion_channel_recording: {
        AssetLabel.nwb: [
            LabelRequirements(
                content_type=ContentType.nwb,
                is_directory=False,
                description="Ion channel experimental electrophysiology recording.",
            ),
        ]
    },
    EntityType.me_type_density: {
        AssetLabel.voxel_densities: [
            LabelRequirements(
                content_type=ContentType.nrrd,
                is_directory=False,
                description="Morpho-electric cell voxel densities.",
            )
        ],
    },
    EntityType.cell_morphology: {
        AssetLabel.morphology: [
            LabelRequirements(
                content_type=ContentType.asc,
                is_directory=False,
                description="Morphology in Neurolucida ASCII format.",
            ),
            LabelRequirements(
                content_type=ContentType.swc,
                is_directory=False,
                description="Morphology in SWC format.",
            ),
            LabelRequirements(
                content_type=ContentType.h5,
                is_directory=False,
                description="Morphology in HDF5 format.",
            ),
        ],
        AssetLabel.morphology_with_spines: [
            LabelRequirements(
                content_type=ContentType.h5,
                is_directory=False,
                description=(
                    "H5 file containing mesh and skeletons of spines. "
                    "Also includes soma mesh, and morphology skeleton."
                ),
            ),
        ],
    },
    EntityType.simulation: {
        AssetLabel.custom_node_sets: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Node set groups for regions, mtypes, etc.",
            )
        ],
        AssetLabel.replay_spikes: [
            LabelRequirements(
                content_type=ContentType.h5,
                is_directory=False,
                description="SONATA spike report used for spike replay during simulation.",
            )
        ],
        AssetLabel.simulation_generation_config: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Single simulation generation configuration.",
            )
        ],
        AssetLabel.sonata_simulation_config: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Simulation SONATA configuration.",
            )
        ],
    },
    EntityType.simulation_campaign: {
        AssetLabel.campaign_generation_config: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Campaign configuration.",
            )
        ],
        AssetLabel.campaign_summary: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Summary of generated campaign listing all created simulation configs.",
            )
        ],
    },
    EntityType.simulation_result: {
        AssetLabel.spike_report: [
            LabelRequirements(
                content_type=ContentType.h5,
                is_directory=False,
                description="Simulation spikes report.",
            )
        ],
        AssetLabel.voltage_report: [
            LabelRequirements(
                content_type=ContentType.h5,
                is_directory=False,
                description="Simulation voltage report.",
            ),
            LabelRequirements(
                content_type=ContentType.nwb,
                is_directory=False,
                description="Simulation voltage report in NWB format.",
            ),
        ],
    },
    EntityType.single_neuron_synaptome: {
        AssetLabel.single_neuron_synaptome_config: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Single neuron synaptome configuration.",
            )
        ]
    },
    EntityType.single_neuron_synaptome_simulation: {
        AssetLabel.single_neuron_synaptome_simulation_data: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description=(
                    "Single neuron synaptome simulation configuration and timeseries output."
                ),
            )
        ]
    },
    EntityType.single_neuron_simulation: {
        AssetLabel.single_neuron_simulation_data: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Single neuron simulation configuration and timeseries output.",
            )
        ]
    },
    EntityType.validation_result: {
        AssetLabel.validation_result_figure: [
            LabelRequirements(
                content_type=ContentType.pdf,
                is_directory=False,
                description="Validation result figure, pdf.",
            ),
            LabelRequirements(
                content_type=ContentType.png,
                is_directory=False,
                description="Validation result figure, png (legacy).",
            ),
        ],
        AssetLabel.validation_result_details: [
            LabelRequirements(
                content_type=ContentType.text,
                is_directory=False,
                description="Log and details about the validation execution.",
            )
        ],
    },
    EntityType.em_cell_mesh: {
        AssetLabel.cell_surface_mesh: [
            LabelRequirements(
                content_type=ContentType.h5,
                is_directory=False,
                description="A triangle mesh describing the surface of a cell in h5 format.",
            ),
            LabelRequirements(
                content_type=ContentType.obj,
                is_directory=False,
                description="A triangle mesh describing the surface of a cell in obj format.",
            ),
        ]
    },
    EntityType.circuit_extraction_campaign: {
        AssetLabel.campaign_generation_config: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Circuit extraction campaign configuration.",
            )
        ],
    },
    EntityType.circuit_extraction_config: {
        AssetLabel.circuit_extraction_config: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Single circuit extraction configuration.",
            )
        ],
    },
    EntityType.skeletonization_campaign: {
        AssetLabel.campaign_generation_config: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Skeletonization campaign configuration.",
            )
        ],
    },
    EntityType.skeletonization_config: {
        AssetLabel.skeletonization_config: [
            LabelRequirements(
                content_type=ContentType.json,
                is_directory=False,
                description="Single skeletonization configuration.",
            )
        ],
    },
}
ALLOWED_ASSET_LABELS_PER_ENTITY |= {
    k: None for k in EntityType if k not in ALLOWED_ASSET_LABELS_PER_ENTITY
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


class PublicationType(StrEnum):
    """The type of of the relation between publication and a scientific artifact.

    entity_source: The artefact is published with this publication.
    component_source: The publication is used to generate the artifact.
    application: The publication uses the artifact.
    """

    entity_source = auto()
    component_source = auto()
    application = auto()


class ExternalSource(StrEnum):
    """External sources that can be used for external urls."""

    channelpedia = auto()
    modeldb = auto()
    icgenealogy = auto()


class ExternalSourceInfo(TypedDict):
    """Additional information for the external source."""

    name: str
    allowed_url: str


EXTERNAL_SOURCE_INFO: dict[ExternalSource, ExternalSourceInfo] = {
    ExternalSource.channelpedia: {
        "name": "Channelpedia",
        "allowed_url": "https://channelpedia.epfl.ch/",
    },
    ExternalSource.icgenealogy: {
        "name": "ICGenealogy",
        "allowed_url": "https://icg.neurotheory.ox.ac.uk/",
    },
    ExternalSource.modeldb: {
        "name": "ModelDB",
        "allowed_url": "https://modeldb.science/",
    },
}


class EMCellMeshType(StrEnum):
    """How an EM cell mesh was created.

    static: The mesh was precomputed at a given level of detail.
    dynamic: The mesh was dynamically generated at query time.
    """

    static = auto()
    dynamic = auto()


class EMCellMeshGenerationMethod(StrEnum):
    """The algorithm generating the mesh from a volume.

    marching_cubes: The marching cubes algorithm.
    """

    marching_cubes = auto()


class AnalysisScale(StrEnum):
    """Rough scale that an activity takes place in. Note: Not equal to CircuitScale."""

    subcellular = auto()
    cellular = auto()
    circuit = auto()
    system = auto()


class ExecutorType(StrEnum):
    single_node_job = auto()
    distributed_job = auto()
    jupyter_notebook = auto()
