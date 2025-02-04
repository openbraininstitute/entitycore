from enum import auto
from typing import Annotated

from sqlalchemy import BigInteger, func, or_
from sqlalchemy.orm import mapped_column
from sqlalchemy.types import VARCHAR, TypeDecorator

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
BIGINT = Annotated[int, mapped_column(BigInteger)]


class EntityType(HyphenStrEnum):
    # name (underscore separated): for table names
    # value (hyphen separated): for endpoints
    reconstruction_morphology = auto()
    species = auto()
    strain = auto()
    experimental_bouton_density = auto()


class AssetStatus(HyphenStrEnum):
    CREATED = auto()
    DELETED = auto()
