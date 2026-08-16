"""Validate _SpecRegistry resolution and spec coverage."""

import re
from itertools import chain
from unittest.mock import MagicMock

import pytest

from app.db.model import Entity
from app.queries.factory import _ensure_facet, _SpecRegistry, query_params_factory
from app.queries.utils import expand_dotted_key

from tests.utils import SERVICE_DIR


def _all_spec_keys() -> set[str]:
    """Derive all valid spec keys by introspecting _SpecRegistry method names."""
    return {
        name.removeprefix("spec_").replace("__", ".")
        for name in dir(_SpecRegistry)
        if name.startswith("spec_")
    }


def _collect_used_spec_keys() -> set[str]:
    """Collect all quoted strings in service files that match a known spec key."""
    all_keys = _all_spec_keys()
    used = {
        match
        for path in SERVICE_DIR.glob("*.py")
        for match in re.findall(r'"([\w.]+)"', path.read_text())
        if match in all_keys
    }
    assert len(used) > 0
    return used


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


def test_no_unused_spec_methods():
    """Every spec_* method in _SpecRegistry must be used by at least one service call."""
    used_keys = _collect_used_spec_keys()
    # Expand dot-notation to also cover parent keys auto-inserted by _expand_filter_keys
    expanded = set(chain.from_iterable(expand_dotted_key(k) for k in used_keys))
    # derivation keys are auto-added by query_params_factory for Entity subclasses
    expanded |= {"generated_derivation", "used_derivation"}

    unused = _all_spec_keys() - expanded
    assert not unused, f"Unused spec_* methods in _SpecRegistry: {unused}"


def test_ensure_facet_raises_on_none():
    """Key without a facet definition must raise when used as a facet key."""
    with pytest.raises(ValueError, match="has no facet"):
        _ensure_facet(None, "some_key")
