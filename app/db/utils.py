import functools
import uuid
from enum import StrEnum
from typing import cast

from pydantic import BaseModel
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    DeclarativeBase,
    InstrumentedAttribute,
    RelationshipProperty,
    class_mapper,
)

from app.db.auth import HasAuth
from app.db.model import (
    Activity,
    Base,
    CellMorphologyProtocol,
    Entity,
    ETypeClassification,
    Identifiable,
    LocationMixin,
    MeasurableEntityMixin,
    MTypeClassification,
    TaskResult,
)
from app.db.types import (
    ALLOWED_ASSET_LABELS_PER_ENTITY,
    ALLOWED_ASSET_LABELS_PER_TASK_RESULT,
    AssetLabel,
    CellMorphologyGenerationType,
    EntityType,
    LabelRequirements,
    ResourceType,
)
from app.logger import L

PublishableBaseModel = Activity | Entity | ETypeClassification | MTypeClassification

PUBLISHABLE_BASE_CLASSES: list[type[PublishableBaseModel]] = [
    Activity,
    Entity,
    ETypeClassification,
    MTypeClassification,
]

MEASURABLE_ENTITIES: dict[str, type[Entity]] = {
    mapper.class_.__tablename__: mapper.class_
    for mapper in Base.registry.mappers
    # skip the single-table subclasses, sharing the table name of their parent
    if issubclass(mapper.class_, MeasurableEntityMixin)
    and issubclass(mapper.class_, Entity)
    and not mapper.single
}
MeasurableEntityType = StrEnum("MeasurableEntity", sorted(MEASURABLE_ENTITIES))

ENTITY_TYPE_TO_CLASS: dict[EntityType, type[Entity]] = {
    EntityType[mapper.class_.__tablename__]: mapper.class_
    for mapper in Base.registry.mappers
    # skip the single-table subclasses, sharing the table name of their parent
    if hasattr(EntityType, mapper.class_.__tablename__) and not mapper.single
}


RESOURCE_TYPE_TO_CLASS: dict[str, type[Identifiable]] = {
    mapper.class_.__tablename__: mapper.class_
    for mapper in Base.registry.mappers
    # skip the single-table subclasses, sharing the table name of their parent
    if mapper.class_.__tablename__ in ResourceType and not mapper.single
}

CELL_MORPHOLOGY_GENERATION_TYPE_TO_CLASS: dict[
    CellMorphologyGenerationType, type[CellMorphologyProtocol]
] = {
    CellMorphologyGenerationType[mapper.polymorphic_identity]: mapper.class_
    for mapper in CellMorphologyProtocol.__mapper__.self_and_descendants
    if mapper.single and mapper.polymorphic_identity  # exclude the base class
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


def _model_kwargs[T: DeclarativeBase](model_cls: type[T], data: dict) -> dict:
    """Build the kwars needed to create or update a database model."""
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
    return model_kwargs


def construct_model[T: DeclarativeBase](model_cls: type[T], data: dict) -> T:
    """Build and return a database model from a dict."""
    model_kwargs = _model_kwargs(model_cls=model_cls, data=data)
    return model_cls(**model_kwargs)


def update_model[T: DeclarativeBase](model: T, data: dict) -> T:
    """Update a database model from a dict, in-place.

    Nested objects are fully replaced, if specified in the given data.
    Unknown attibutes are ignored.
    """
    model_cls = model.__class__
    model_kwargs = _model_kwargs(model_cls=model_cls, data=data)
    for key, value in model_kwargs.items():
        setattr(model, key, value)
    return model


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


def get_authorized_project_id_declaring_class(
    db_model_class: type[Identifiable],
) -> type[HasAuth] | None:
    """Return the class that has a table with project id or None."""
    if not has_project_id_in_columns(db_model_class):
        return None

    return class_mapper(db_model_class).get_property("authorized_project_id").parent.class_


@functools.cache
def get_entity_types(db_model_class: type[Base]) -> tuple[EntityType, ...]:
    """Return the sorted entity types of an ORM class and of its subclasses.

    The result is cached, and it's a tuple so that it can't be modified by the callers.

    Raises:
        TypeError: if db_model_class isn't an entity class.

    Example:
        >>> get_entity_types(ElectricalRecording)
        ('electrical_cell_recording', 'electrical_recording', 'ion_channel_recording')
    """
    entity_types = tuple(
        sorted(
            entity_type
            for entity_type, entity_class in ENTITY_TYPE_TO_CLASS.items()
            if issubclass(entity_class, db_model_class)
        )
    )
    if not entity_types:
        msg = f"{db_model_class.__name__} is not an entity class"
        raise TypeError(msg)
    return entity_types


def allowed_asset_labels_for(entity: Entity) -> dict[AssetLabel, list[LabelRequirements]] | None:
    if entity.type == EntityType.task_result:
        return ALLOWED_ASSET_LABELS_PER_TASK_RESULT.get(cast("TaskResult", entity).task_result_type)
    return ALLOWED_ASSET_LABELS_PER_ENTITY.get(entity.type)
