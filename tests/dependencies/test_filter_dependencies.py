from typing import Annotated

import pytest
import sqlalchemy as sa

from app.db.model import CellMorphology, Species
from app.dependencies.filter import _flatten_fields, _unflatten
from app.filters.base import CustomFilter, Prefix, nested_filter_type, nested_prefix
from app.filters.cell_morphology import CellMorphologyFilter


class _InnerFilter(CustomFilter):
    name: str | None = None
    order_by: list[str] = []  # ruff:ignore[mutable-class-default]

    class Constants(CustomFilter.Constants):
        model = Species


class _OtherFilter(CustomFilter):
    name: str | None = None

    class Constants(CustomFilter.Constants):
        model = Species


class _OuterFilter(CustomFilter):
    inner: _InnerFilter | None = None

    class Constants(CustomFilter.Constants):
        model = Species


class _DuplicatePrefixFilter(CustomFilter):
    first: Annotated[_InnerFilter | None, Prefix(value="shared")] = None
    second: Annotated[_OtherFilter | None, Prefix(value="shared")] = None

    class Constants(CustomFilter.Constants):
        model = Species


def test_flatten_fields_rejects_duplicate_query_params():
    with pytest.raises(ValueError, match="Duplicate query parameter 'shared__name'"):
        _flatten_fields(_DuplicatePrefixFilter)


def test_flatten_fields_skips_nested_order_by():
    fields = _flatten_fields(_OuterFilter)

    assert "inner__name" in fields
    assert "inner__order_by" not in fields


def test_unflatten_ignores_nested_order_by():
    filter_ = _unflatten(_OuterFilter, {"inner__name": "x", "inner__order_by": ["name"]})

    assert isinstance(filter_, _OuterFilter)
    assert isinstance(filter_.inner, _InnerFilter)
    assert filter_.inner.name == "x"
    assert filter_.inner.order_by == []


def test_nested_filter_type_detects_optional_filter():
    assert nested_filter_type(_InnerFilter | None) is _InnerFilter
    assert nested_filter_type(_InnerFilter) is _InnerFilter


def test_nested_filter_type_ignores_non_filters_and_unions_of_several_filters():
    assert nested_filter_type(_InnerFilter | _OtherFilter | None) is None
    assert nested_filter_type(str | None) is None
    assert nested_filter_type(Annotated[str, "meta"] | None) is None  # pyright: ignore[reportOperatorIssue]


def test_nested_filter_type_rejects_annotated_inside_union():
    with pytest.raises(TypeError, match="Wrap the whole union in Annotated"):
        nested_filter_type(Annotated[_InnerFilter, Prefix(value="shared")] | None)  # pyright: ignore[reportOperatorIssue]


def test_nested_prefix_uses_prefix_metadata_or_field_name():
    class _Parent(CustomFilter):
        prefixed: Annotated[_InnerFilter | None, Prefix(value="custom")] = None
        after_other_metadata: Annotated[_InnerFilter | None, "doc", Prefix(value="custom")] = None
        plain: _InnerFilter | None = None

        class Constants(CustomFilter.Constants):
            model = Species

    assert nested_prefix("prefixed", _Parent.model_fields["prefixed"]) == "custom"
    assert nested_prefix("after_other_metadata", _Parent.model_fields["after_other_metadata"]) == (
        "custom"
    )
    assert nested_prefix("plain", _Parent.model_fields["plain"]) == "plain"


def test_sort_rejects_nested_part_that_is_not_a_filter():
    invalid_filter = CellMorphologyFilter.model_construct(order_by=["name__pref_label"])

    with pytest.raises(ValueError, match="Unsupported ordering part 'name'"):
        invalid_filter.sort(sa.select(CellMorphology))
