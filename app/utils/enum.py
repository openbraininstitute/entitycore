"""Custom enum."""

from collections.abc import Sequence
from enum import StrEnum
from typing import cast


class HyphenStrEnum(StrEnum):
    """Enum where members are also (and must be) strings.

    When using auto(), the resulting value is the hyphenated lower-cased version of the member name.
    """

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[str]) -> str:  # noqa: ARG004
        """Return the hyphenated lower-cased version of the member name."""
        return name.lower().replace("_", "-")


class UpperStrEnum(StrEnum):
    """Enum where members are also (and must be) strings.

    When using auto(), the resulting value is the upper-cased version of the member name.
    """

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[str]) -> str:  # noqa: ARG004
        """Return the upper-cased version of the member name."""
        return name.upper()


def combine_str_enums(name: str, enums: Sequence[type[StrEnum]]) -> type[StrEnum]:
    """Combine mutliple StrEnum into a single one."""
    members = {e.name: e.value for enum in enums for e in enum.__members__.values()}
    return cast("type[StrEnum]", StrEnum(name, members))
