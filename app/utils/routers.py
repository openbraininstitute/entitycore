from enum import StrEnum
from typing import TYPE_CHECKING, Any

from app.db.types import EntityType, ResourceType


def _convert_resource_type_to_route(name):
    if name == "mtype_class":
        return "mtype"
    if name == "etype_class":
        return "etype"
    return name.replace("_", "-")


if not TYPE_CHECKING:
    # EntityRoute (hyphen-separated) <-> EntityType (underscore_separated)
    EntityRoute = StrEnum(
        "EntityRoute", {item.name: item.name.replace("_", "-") for item in EntityType}
    )
    ResourceRoute = StrEnum(
        "ResourceRoute",
        {item.name: _convert_resource_type_to_route(item.name) for item in ResourceType},
    )
else:
    EntityRoute = StrEnum
    ResourceRoute = StrEnum


def entity_route_to_type(entity_route: EntityRoute) -> EntityType:
    return EntityType[entity_route.name]


def route_to_type(route: ResourceRoute) -> Any:
    return ResourceType[route.name]
