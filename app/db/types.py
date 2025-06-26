from enum import StrEnum, auto
from pathlib import Path
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
    neurolucida = auto()
    swc = auto()
    hdf5 = auto()
    cell_composition_summary = auto()
    cell_composition_volumes = auto()
    single_neuron_synaptome_config = auto()
    single_neuron_synaptome_simulation_io_result = auto()
    single_cell_simulation_data = auto()
    sonata_circuit = auto()
    nwb = auto()
    neuron_hoc = auto()
    emodel_parametrization_optimization_output = auto()
    sonata_simulation_config = auto()
    simulation_generation_config = auto()
    custom_node_sets = auto()
    campaign_generation_config = auto()
    campaign_summary = auto()
    replay_spikes = auto()
    voltage_report = auto()
    spike_report = auto()
    neuron_mechanism = auto()
    brain_atlas_annotation = auto()
    brain_region_mesh = auto()


def _suffix(suffix: str):
    return lambda asset: Path(asset.path).suffix.lower() == suffix


def _contenttype(contenttype: ContentType):
    return lambda asset: asset.content_type == contenttype


def _and(*functions):
    return lambda asset: all(f(asset) for f in functions)


def _require_directory(asset):
    return asset.is_directory


ALLOWED_ASSET_LABELS_PER_ENTITY = {
    EntityType.reconstruction_morphology: {
        AssetLabel.neurolucida: _and(_suffix(".asc"), _contenttype(ContentType.asc)),
        AssetLabel.swc: _and(_suffix(".swc"), _contenttype(ContentType.swc)),
        AssetLabel.hdf5: _and(_suffix(".h5"), _contenttype(ContentType.h5)),
    },
    EntityType.cell_composition: {
        AssetLabel.cell_composition_summary: None,
        AssetLabel.cell_composition_volumes: None,
    },
    EntityType.single_neuron_synaptome: {
        AssetLabel.single_neuron_synaptome_config: None,
    },
    EntityType.single_neuron_synaptome_simulation: {
        AssetLabel.single_neuron_synaptome_simulation_io_result: None,
    },
    EntityType.single_neuron_simulation: {
        AssetLabel.single_cell_simulation_data: None,
    },
    EntityType.circuit: {
        AssetLabel.sonata_circuit: _require_directory,
    },
    EntityType.electrical_cell_recording: {
        AssetLabel.nwb: None,
    },
    EntityType.emodel: {
        AssetLabel.neuron_hoc: None,
        AssetLabel.emodel_parametrization_optimization_output: None,
    },
    EntityType.simulation: {
        AssetLabel.sonata_simulation_config: None,
        AssetLabel.simulation_generation_config: None,
        AssetLabel.custom_node_sets: None,
        AssetLabel.replay_spikes: None,
    },
    EntityType.simulation_campaign: {
        AssetLabel.campaign_generation_config: None,
        AssetLabel.campaign_summary: None,
    },
    EntityType.simulation_result: {
        AssetLabel.voltage_report: None,
        AssetLabel.spike_report: None,
    },
    EntityType.ion_channel_model: {
        AssetLabel.neuron_mechanism: None,
    },
    EntityType.brain_atlas: {
        AssetLabel.brain_atlas_annotation: None,
    },
    EntityType.brain_atlas_region: {
        AssetLabel.brain_region_mesh: None,
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
