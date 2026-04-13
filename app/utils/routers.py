from typing import Any

from app.db.types import EntityType, ResourceType
from app.routers.types import EntityRoute, ResourceRoute


def _convert_resource_type_to_route(name):
    if name == "mtype_class":
        return "mtype"
    if name == "etype_class":
        return "etype"
    return name.replace("_", "-")


def entity_route_to_type(entity_route: EntityRoute) -> EntityType:
    return EntityType[entity_route.name]


def route_to_type(route: ResourceRoute) -> Any:
    return ResourceType[route.name]
