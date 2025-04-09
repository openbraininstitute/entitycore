from enum import StrEnum

from app.db.model import Base, MeasurableEntity

MEASURABLE_ENTITIES: dict[str, type[MeasurableEntity]] = {
    mapper.class_.__tablename__: mapper.class_
    for mapper in Base.registry.mappers
    if issubclass(mapper.class_, MeasurableEntity) and mapper.class_.__tablename__
}
MeasurableEntityType = StrEnum("MeasurableEntity", list(MEASURABLE_ENTITIES))
