from abc import ABC
from enum import auto
from typing import Annotated, Any

from pydantic import BaseModel
from sqlalchemy import ARRAY, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column
from sqlalchemy.types import VARCHAR, TypeDecorator

from app.logger import L
from app.schemas.base import MeasurementGroup, PointLocationBase
from app.utils.enum import StrEnum


class PydanticJSONB[T: BaseModel](TypeDecorator, ABC):
    """Base class for storing Pydantic models and lists of Pydantic models in a JSONB column."""

    impl = JSONB
    cache_ok = True
    model_class: type[T]

    def _dump_item(self, item: T | dict) -> dict:
        if isinstance(item, dict):
            L.warning("Possible validation roundtrip for {}", self.model_class)
            # possible validation roundtrip that could be avoided
            # if the dict has been generated using model_dump
            item = self.model_class.model_validate(item)
        if not isinstance(item, self.model_class):
            err = f"Expected {self.model_class}, got {type(item)}"
            raise TypeError(err)
        return item.model_dump()

    def _load_item(self, item: dict) -> T:
        return self.model_class.model_validate(item)


class PydanticDictJSONB[T: BaseModel](PydanticJSONB[T], ABC):
    """Store a Pydantic model in a JSONB column."""

    def process_bind_param(self, value: T | dict | None, dialect) -> dict | None:  # noqa: ARG002
        return self._dump_item(value) if value is not None else None

    def process_result_value(self, value: dict | None, dialect) -> T | None:  # noqa: ARG002
        return self._load_item(value) if value is not None else None


class PydanticListJSONB[T: BaseModel](PydanticJSONB[T], ABC):
    """Store a list of Pydantic models in a JSONB column."""

    def process_bind_param(self, value: list[T | dict] | None, dialect) -> list[dict] | None:  # noqa: ARG002
        return [self._dump_item(item) for item in value] if value is not None else None

    def process_result_value(self, value: list[dict] | None, dialect) -> list[T] | None:  # noqa: ARG002
        return [self._load_item(item) for item in value] if value is not None else None


class PointLocationType(PydanticDictJSONB[PointLocationBase]):
    model_class = PointLocationBase


class MeasurementCollectionType(PydanticListJSONB[MeasurementGroup]):
    model_class = MeasurementGroup


BIGINT = Annotated[int, mapped_column(BigInteger)]
JSON_DICT = Annotated[dict[str, Any], mapped_column(JSONB)]
STRING_LIST = Annotated[list[str], mapped_column(ARRAY(VARCHAR))]
POINT_LOCATION = Annotated[PointLocationBase, mapped_column(PointLocationType)]
MEASUREMENT_COLLECTION = Annotated[list[MeasurementGroup], mapped_column(MeasurementCollectionType)]


class EntityType(StrEnum):
    """Entity types."""

    analysis_software_source_code = auto()
    emodel = auto()
    experimental_bouton_density = auto()
    experimental_neuron_density = auto()
    experimental_synapses_per_connection = auto()
    memodel = auto()
    mesh = auto()
    reconstruction_morphology = auto()
    single_cell_experimental_trace = auto()
    single_neuron_simulation = auto()
    single_neuron_synaptome = auto()
    single_neuron_synaptome_simulation = auto()


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
