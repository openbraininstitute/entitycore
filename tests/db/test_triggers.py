from sqlalchemy.orm import DeclarativeBase

from app.db import triggers as test_module
from app.db.model import Base, Entity


def _get_tablename_to_class() -> dict[str, type[DeclarativeBase]]:
    """Map each table name to the corresponding class, excluding single table inheritance."""
    return {
        mapper.class_.__tablename__: mapper.class_
        for mapper in Base.registry.mappers
        if mapper.polymorphic_identity in {mapper.class_.__tablename__, None}
    }


def _find_protected_relationships(
    source_base: type[DeclarativeBase], target_base: type[DeclarativeBase]
) -> list[tuple[type[DeclarativeBase], str, type[DeclarativeBase]]]:
    """Return a list of protected relationships as (model, field_name)."""
    tablename_to_class = _get_tablename_to_class()
    results = []
    for mapper in Base.registry.mappers:
        source_class = mapper.class_
        if not issubclass(source_class, source_base):
            continue
        for col in mapper.local_table.columns:
            if col.key == "id":
                continue
            for fk in col.foreign_keys:
                target_col = fk.column
                target_table = target_col.table
                target_class = tablename_to_class.get(target_table.name)
                if not target_class or not issubclass(target_class, target_base):
                    continue
                results.append((source_class, col.key))
    return results


def test_protected_entity_relationships():
    """Test that the list of protected_relationships is complete."""
    actual = test_module.protected_entity_relationships
    expected = _find_protected_relationships(source_base=Entity, target_base=Entity)

    missing = set(expected).difference(actual)
    unexpected = set(actual).difference(expected)

    assert missing == set()
    assert unexpected == set()
    assert len(actual) == len(expected)
