from enum import auto
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ARRAY, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column
from sqlalchemy.types import VARCHAR, TypeDecorator

from app.utils.enum import StrEnum


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
    emodel = auto()
    cell_composition = auto()
    experimental_bouton_density = auto()
    experimental_neuron_density = auto()
    experimental_synapses_per_connection = auto()
    memodel = auto()
    mesh = auto()
    me_type_density = auto()
    reconstruction_morphology = auto()
    electrical_cell_recording = auto()
    electrical_recording_stimulus = auto()
    single_neuron_simulation = auto()
    single_neuron_synaptome = auto()
    single_neuron_synaptome_simulation = auto()
    ion_channel_model = auto()
    subject = auto()
    validation_result = auto()


class AgentType(StrEnum):
    """Agent types."""

    person = auto()
    organization = auto()


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


class AssetLabel(StrEnum):
    neurolucida = auto()
    swc = auto()
    hdf5 = auto()
    cell_composition_summary = auto()
    cell_composition_volumes = auto()
    single_neuron_synaptome_config = auto()
    single_neuron_synaptome_simulation_io_result = auto()
    single_cell_simulation_data = auto()


ALLOWED_ASSET_LABELS_PER_ENTITY = {
    EntityType.reconstruction_morphology: {
        AssetLabel.neurolucida,
        AssetLabel.swc,
        AssetLabel.hdf5,
    },
    EntityType.cell_composition: {
        AssetLabel.cell_composition_summary,
        AssetLabel.cell_composition_volumes,
    },
    EntityType.single_neuron_synaptome: {AssetLabel.single_neuron_synaptome_config},
    EntityType.single_neuron_synaptome_simulation: {
        AssetLabel.single_neuron_synaptome_simulation_io_result
    },
    EntityType.single_neuron_simulation: {AssetLabel.single_cell_simulation_data},
}
