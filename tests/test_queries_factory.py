"""Validate that _SpecRegistry resolves all keys without alias collisions.

Uses a mock model class so that all spec keys can be resolved together in one call.
The lambdas inside JoinSpec are never invoked — only the alias wiring is tested.
"""

from unittest.mock import MagicMock

import pytest

from app.db.model import Entity
from app.queries.factory import _SpecRegistry, query_params_factory


def _all_spec_keys() -> list[str]:
    """Derive all valid spec keys by introspecting _SpecRegistry method names."""
    return [
        name.removeprefix("spec_").replace("__", ".")
        for name in dir(_SpecRegistry)
        if name.startswith("spec_")
    ]


def test_all_specs_resolve_without_alias_collisions():
    """Resolve every spec key on a mock model; verify no alias collisions."""
    mock_model = MagicMock()
    aliases: dict = {}
    registry = _SpecRegistry(mock_model, aliases)

    for key in _all_spec_keys():
        registry.resolve(key)

    # Named aliases must have distinct objects per name
    for cls, value in aliases.items():
        if isinstance(value, dict):
            objects = list(value.values())
            assert len(objects) == len({id(o) for o in objects}), (
                f"{cls.__name__} has duplicate alias objects: {list(value.keys())}"
            )


def test_query_params_factory_entity_model():
    """Entity subclass: derivation keys are auto-appended and aliases resolved."""
    facet_params, join_specs, _aliases = query_params_factory(
        db_model_class=Entity,
        facet_keys=["created_by", "updated_by", "contribution"],
        filter_keys=["created_by", "updated_by", "contribution"],
    )
    assert "generated_derivation" in join_specs
    assert "used_derivation" in join_specs
    assert set(facet_params) == {"created_by", "updated_by", "contribution"}


def test_query_params_factory_non_entity_model():
    """Non-entity model: no derivation keys appended."""
    mock_model = MagicMock()
    _facet_params, join_specs, _aliases = query_params_factory(
        db_model_class=mock_model,
        facet_keys=["created_by", "updated_by"],
        filter_keys=["created_by", "updated_by"],
    )
    assert "generated_derivation" not in join_specs
    assert "used_derivation" not in join_specs


def test_query_params_factory_facet_keys_must_be_in_filter_keys():
    """Facet keys not present in filter_keys must raise."""
    mock_model = MagicMock()
    with pytest.raises(ValueError, match="Facet keys missing from filter_keys"):
        query_params_factory(
            db_model_class=mock_model,
            facet_keys=["created_by", "unknown"],
            filter_keys=["created_by"],
        )


def test_query_params_factory_unknown_key_raises():
    """Unknown spec key must raise."""
    mock_model = MagicMock()
    with pytest.raises(ValueError, match="Unknown key"):
        query_params_factory(
            db_model_class=mock_model,
            facet_keys=[],
            filter_keys=["nonexistent_key"],
        )
