"""Tests for app.queries.filter."""

from unittest.mock import MagicMock

import pytest

from app.queries.filter import filter_from_db


def test_filter_from_db_raises_on_invalid_facet_key():
    """Facet key not present in join_specs must raise."""
    query = MagicMock()
    filter_model = MagicMock()
    with pytest.raises(RuntimeError, match="Not allowed as facet_key"):
        filter_from_db(query, filter_model, join_specs={}, facet_key="nonexistent")
