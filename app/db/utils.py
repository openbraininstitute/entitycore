import uuid
from enum import StrEnum

from pydantic import BaseModel
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, RelationshipProperty

from app.db.model import Base, Entity, Identifiable, LocationMixin, MeasurableEntity
from app.db.types import EntityType, ResourceType
from app.logger import L

MEASURABLE_ENTITIES: dict[str, type[MeasurableEntity]] = {
    mapper.class_.__tablename__: mapper.class_
    for mapper in Base.registry.mappers
    if issubclass(mapper.class_, MeasurableEntity) and mapper.class_.__tablename__
}
MeasurableEntityType = StrEnum("MeasurableEntity", sorted(MEASURABLE_ENTITIES))

ENTITY_TYPE_TO_CLASS: dict[EntityType, type[Entity]] = {
    EntityType[mapper.class_.__tablename__]: mapper.class_
    for mapper in Base.registry.mappers
    if hasattr(EntityType, mapper.class_.__tablename__)
}

RESOURCE_TYPE_TO_CLASS: dict[str, type[Identifiable]] = {
    mapper.class_.__tablename__: mapper.class_
    for mapper in Base.registry.mappers
    if mapper.class_.__tablename__ in ResourceType
}


entity_type_with_brain_region_enum_members = {
    member.name: member.value
    for member, cls in ENTITY_TYPE_TO_CLASS.items()
    if issubclass(cls, LocationMixin)
}

EntityTypeWithBrainRegion = StrEnum(
    "EntityTypeWithBrainRegion",
    sorted(entity_type_with_brain_region_enum_members),
)


def construct_model[T: DeclarativeBase](model_cls: type[T], data: dict) -> T:
    """Build and return a database model from a dict."""
    model_kwargs = {}
    for attr_name, attr_val in data.items():
        if not (attr := getattr(model_cls, attr_name, None)):
            L.debug("Attribute not found: {}.{}", model_cls, attr_name)
            continue
        if isinstance(getattr(attr, "descriptor", None), hybrid_property):
            continue
        if not isinstance(attr, InstrumentedAttribute):
            L.warning("Attribute ignored: {}.{} -> {}", model_cls, attr_name, type(attr))
            continue
        if isinstance(getattr(attr, "property", None), RelationshipProperty):
            related_cls = attr.property.mapper.class_
            if isinstance(attr_val, list):
                # One-to-many or many-to-many
                model_kwargs[attr_name] = [construct_model(related_cls, item) for item in attr_val]
            elif isinstance(attr_val, dict):
                # One-to-one or many-to-one
                model_kwargs[attr_name] = construct_model(related_cls, attr_val)
            else:
                L.warning("Unexpected attribute type: {}", type(attr_val))
                model_kwargs[attr_name] = attr_val
        else:
            model_kwargs[attr_name] = attr_val
    return model_cls(**model_kwargs)


def load_db_model_from_pydantic[I: DeclarativeBase](
    json_model: BaseModel,
    db_model_class: type[I],
    authorized_project_id: uuid.UUID | None,
    created_by_id: uuid.UUID | None,
    updated_by_id: uuid.UUID | None,
    ignore_attributes: set[str] | None = None,
    *,
    exclude_defaults: bool = False,
) -> I:
    data = json_model.model_dump(by_alias=True, exclude_defaults=exclude_defaults)

    if created_by_id or updated_by_id:
        data["created_by_id"] = created_by_id
        data["updated_by_id"] = updated_by_id

    if has_project_id_in_columns(db_model_class):
        data["authorized_project_id"] = authorized_project_id

    if ignore_attributes:
        data = {k: v for k, v in data.items() if k not in ignore_attributes}

    return construct_model(db_model_class, data)


def has_project_id_in_columns(db_model_class) -> bool:
    """Return True if project id in table or parent tables."""
    return "authorized_project_id" in db_model_class.__mapper__.columns


def get_declaring_class[I: Identifiable](
    db_model_class: type[I], column_name: str
) -> type[I] | None:
    """Return the class that has a table with project id or None."""
    if not has_project_id_in_columns(db_model_class):
        return None

    declaring_table = db_model_class.__mapper__.columns[column_name].table

    # Iterate all mappers registered with the Base registry
    for mapper in db_model_class.registry.mappers:
        if mapper.local_table is declaring_table:
            return mapper.class_

    return None
