import uuid
from enum import StrEnum

from pydantic import BaseModel
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, RelationshipProperty

from app.db.model import Base, Entity, Identifiable, MeasurableEntity
from app.logger import L

MEASURABLE_ENTITIES: dict[str, type[MeasurableEntity]] = {
    mapper.class_.__tablename__: mapper.class_
    for mapper in Base.registry.mappers
    if issubclass(mapper.class_, MeasurableEntity) and mapper.class_.__tablename__
}
MeasurableEntityType = StrEnum("MeasurableEntity", list(MEASURABLE_ENTITIES))


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


def load_db_model_from_pydantic[I: Identifiable](
    json_model: BaseModel,
    db_model_class: type[I],
    authorized_project_id: uuid.UUID | None,
    created_by_id: uuid.UUID | None = None,
    updated_by_id: uuid.UUID | None = None,
) -> I:
    data = json_model.model_dump(by_alias=True)
    if issubclass(db_model_class, Entity):
        data |= {
            "authorized_project_id": authorized_project_id,
            "createdBy_id": created_by_id,
            "updatedBy_id": updated_by_id,
        }
    return construct_model(db_model_class, data)
