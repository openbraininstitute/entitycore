"""Tests for app.queries.filter."""

from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from app.db.model import CellMorphology, EModel
from app.queries.factory import query_params_factory
from app.queries.filter import _is_single_valued_join, filter_from_db, multi_valued_facet_keys


def test_filter_from_db_raises_on_invalid_facet_key():
    """Facet key not present in join_specs must raise."""
    query = MagicMock()
    filter_model = MagicMock()
    with pytest.raises(RuntimeError, match="Not allowed as facet_key"):
        filter_from_db(query, filter_model, join_specs={}, facet_keys=["nonexistent"])


@pytest.mark.parametrize(
    ("db_model_class", "facet_keys", "expected"),
    [
        (
            CellMorphology,
            [
                "brain_region",
                "subject.species",
                "subject.strain",
                "created_by",
                "contribution",
                "mtype",
                "cell_morphology_protocol",
            ],
            {"contribution", "mtype"},
        ),
        (
            EModel,
            ["species", "strain", "exemplar_morphology", "etype", "mtype", "ion_channel_model"],
            {"etype", "mtype", "ion_channel_model"},
        ),
    ],
)
def test_multi_valued_facet_keys(db_model_class, facet_keys, expected):
    facet_query_params, join_specs, _ = query_params_factory(
        db_model_class=db_model_class, facet_keys=facet_keys, filter_keys=facet_keys
    )

    result = multi_valued_facet_keys(sa.select(db_model_class), join_specs, facet_query_params)

    assert result == expected


_METADATA = sa.MetaData()
_PARENT = sa.Table("parent", _METADATA, sa.Column("id", sa.Integer, primary_key=True))
_CHILD = sa.Table(
    "child",
    _METADATA,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("parent_id", sa.ForeignKey("parent.id")),
)
_LINK = sa.Table(
    "link",
    _METADATA,
    sa.Column("child_id", sa.ForeignKey("child.id"), primary_key=True),
    sa.Column("parent_id", sa.ForeignKey("parent.id"), primary_key=True),
)


@pytest.mark.parametrize(
    ("target", "onclause", "expected"),
    [
        (_PARENT, _CHILD.c.parent_id == _PARENT.c.id, True),
        (_CHILD, _PARENT.c.id == _CHILD.c.parent_id, False),
        (_CHILD, _CHILD.c.parent_id > _PARENT.c.id, False),
        (_LINK, _PARENT.c.id == _LINK.c.parent_id, False),
        (_PARENT, sa.and_(_CHILD.c.parent_id == _PARENT.c.id, _CHILD.c.id > 1), False),
        (_PARENT, None, False),
        ("not a selectable", _CHILD.c.parent_id == _PARENT.c.id, False),
    ],
)
def test_is_single_valued_join(target, onclause, expected):
    assert _is_single_valued_join(target, onclause) is expected
