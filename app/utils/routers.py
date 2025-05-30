from enum import StrEnum
from typing import TYPE_CHECKING

from app.db.types import EntityType

if not TYPE_CHECKING:
    # EntityRoute (hyphen-separated) <-> EntityType (underscore_separated)
    EntityRoute = StrEnum(
        "EntityRoute", {item.name: item.name.replace("_", "-") for item in EntityType}
    )
else:
    EntityRoute = StrEnum


def entity_route_to_type(entity_route: EntityRoute) -> EntityType:
    return EntityType[entity_route.name]
