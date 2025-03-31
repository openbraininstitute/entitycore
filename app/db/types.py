from enum import auto
from typing import Annotated, Any

from sqlalchemy import ARRAY, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column
from sqlalchemy.types import VARCHAR, TypeDecorator

from app.utils.enum import HyphenStrEnum, StrEnum


class PointLocationType(TypeDecorator):
    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: ARG002, PLR6301
        if value is None:
            return None

        return value.model_dump()

    def process_result_value(self, value, dialect):  # noqa: ARG002, PLR6301
        if value is None:
            return None

        from app.schemas.base import PointLocationBase  # noqa: PLC0415

        return PointLocationBase(**value)


PointLocation = Annotated[PointLocationType, "PointLocation"]

BIGINT = Annotated[int, mapped_column(BigInteger)]
JSON_DICT = Annotated[dict[str, Any], mapped_column(JSONB)]
STRING_LIST = Annotated[list[str], mapped_column(ARRAY(VARCHAR))]


class EntityType(HyphenStrEnum):
    """Entities that are directly exposed through the API.

    For each entry:

    - name (underscore separated): for table names and S3 keys
    - value (hyphen separated): for endpoints
    """

    emodel = auto()
    experimental_bouton_density = auto()
    experimental_neuron_density = auto()
    experimental_synapses_per_connection = auto()
    mesh = auto()
    reconstruction_morphology = auto()
    single_cell_experimental_trace = auto()


class AssetStatus(HyphenStrEnum):
    CREATED = auto()
    DELETED = auto()


class SingleNeuronSimulationStatus(StrEnum):
    started = auto()
    failure = auto()
    success = auto()


class Sex(StrEnum):
    male = auto()
    female = auto()


class ElectricalRecordingType(StrEnum):
    intracellular = auto()
    extracellular = auto()
    both = auto()
