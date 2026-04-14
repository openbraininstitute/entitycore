from typing import Any

from app.db.types import EntityType, ResourceType
from app.routers.types import EntityRoute, ResourceRoute


def entity_route_to_type(entity_route: EntityRoute) -> EntityType:
    return EntityType[entity_route.name]


def route_to_type(route: ResourceRoute) -> Any:
    if route == "mtype":
        return ResourceType["mtype_class"]
    if route == "etype":
        return ResourceType["etype_class"]
    return ResourceType[route.name]
