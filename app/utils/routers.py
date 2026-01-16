from enum import StrEnum
from typing import TYPE_CHECKING, Any

from app.db.types import ActivityType, EntityType, GlobalType, ResourceType

# resources not exposed via dedicated endpoints
NOT_ROUTABLE_RESOURCES = {
    EntityType.analysis_software_source_code,
    EntityType.electrical_recording,
    EntityType.me_type_density,
    EntityType.scientific_artifact,
    GlobalType.ion,
}


def _convert_resource_type_to_route(name):
    if name == "mtype_class":
        return "mtype"
    if name == "etype_class":
        return "etype"
    return name.replace("_", "-")


def _to_hyphened_dict(type_: type[StrEnum]) -> dict[str, str]:
    # items are filtered and values are hiphen-separated
    return {
        item.name: _convert_resource_type_to_route(item.name)
        for item in type_
        if item not in NOT_ROUTABLE_RESOURCES
    }


if not TYPE_CHECKING:
    # EntityRoute (hyphen-separated) <-> EntityType (underscore_separated)
    EntityRoute = StrEnum("EntityRoute", _to_hyphened_dict(EntityType))
    ActivityRoute = StrEnum("ActivityRoute", _to_hyphened_dict(ActivityType))
    GlobalRoute = StrEnum("GlobalRoute", _to_hyphened_dict(GlobalType))
    ResourceRoute = StrEnum("ResourceRoute", _to_hyphened_dict(ResourceType))
else:
    EntityRoute = StrEnum
    GlobalRoute = StrEnum
    ResourceRoute = StrEnum
    ActivityRoute = StrEnum


def entity_route_to_type(entity_route: EntityRoute) -> EntityType:
    return EntityType[entity_route.name]


def route_to_type(route: ResourceRoute) -> Any:
    return ResourceType[route.name]
