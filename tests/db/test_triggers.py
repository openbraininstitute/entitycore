import pytest
from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger
from sqlalchemy.orm import DeclarativeBase

from app.db import triggers as test_module
from app.db.model import Base, Circuit, Entity, Subject


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


@pytest.mark.parametrize("name", ["a", "a" * 63])
def test__check_name_length(name):
    result = test_module._check_name_length(name)
    assert result == name


@pytest.mark.parametrize(
    ("name", "expected_err"),
    [
        ("", "Minimum identifier length is 1 bytes, but .* is 0"),
        ("a" * 64, "Maximum identifier length is 63 bytes, but .* is 64"),
    ],
)
def test__check_name_length_raises(name, expected_err):
    with pytest.raises(ValueError, match=expected_err):
        test_module._check_name_length(name)


def test_description_vector_trigger():
    model = Subject
    result = test_module.description_vector_trigger(
        model=model,
        signature=f"{model.__tablename__}_description_vector",
        target_field="description_vector",
        fields=["description", "name"],
    )
    assert isinstance(result, PGTrigger)

    with pytest.raises(TypeError, match="At least one field required"):
        test_module.description_vector_trigger(
            model=model,
            signature=f"{model.__tablename__}_description_vector",
            target_field="description_vector",
            fields=[],
        )

    with pytest.raises(TypeError, match="'unknown' is not a column of Subject"):
        test_module.description_vector_trigger(
            model=model,
            signature=f"{model.__tablename__}_description_vector",
            target_field="description_vector",
            fields=["unknown"],
        )


def test_unauthorized_private_reference_function():
    result = test_module.unauthorized_private_reference_function(Circuit, "atlas_id")
    assert isinstance(result, PGFunction)


def test_unauthorized_private_reference_trigger():
    result = test_module.unauthorized_private_reference_trigger(Circuit, "atlas_id")
    assert isinstance(result, PGTrigger)
