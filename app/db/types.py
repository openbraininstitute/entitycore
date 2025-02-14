from typing import Annotated

from sqlalchemy import func, or_
from sqlalchemy.types import VARCHAR, TypeDecorator


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
