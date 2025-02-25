from enum import StrEnum, auto
from typing import Annotated, Any

from sqlalchemy import BigInteger, func, or_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column
from sqlalchemy.types import VARCHAR, TypeDecorator

from app.schemas.base import PointLocationBase
from app.utils.enum import HyphenStrEnum


class StringListType(TypeDecorator):
    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: ARG002, PLR6301
        if value is not None:
            return ",".join(value)
        return None

    def process_result_value(self, value, dialect):  # noqa: ARG002, PLR6301
        if value is not None:
            return value.split(",")
        return None

    @staticmethod
    def is_equal(column, value):
        return func.strpos(column, value) > 0

    @staticmethod
    def in_(column, values):
        return or_(*[StringList.is_equal(column, value) for value in values])


StringList = Annotated[StringListType, "StringList"]


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

        return PointLocationBase(**value)


PointLocation = Annotated[PointLocationType, "PointLocation"]


BIGINT = Annotated[int, mapped_column(BigInteger)]
JSONDICT = Annotated[dict[str, Any], mapped_column(JSONB)]


class EntityType(StrEnum):
    """Entity types that are directly exposed through the API.

    For each entry:

    - name (underscore separated): used for table names
    - value (hyphen separated): used for endpoints  # TODO: use it to make everything kebab-case
    """

    experimental_bouton_density = auto()
    experimental_neuron_density = auto()
    experimental_synapses_per_connection = auto()
    reconstruction_morphology = auto()


class AssetStatus(HyphenStrEnum):
    CREATED = auto()
    DELETED = auto()
