"""Validate alias creation and helper functions."""

import sqlalchemy as sa

from app.db.model import BrainRegion, Entity
from app.queries.alias_registry import build_aliases, get_alias, merge_aliases


def test_get_alias_identity():
    """get_alias returns the same object for the same (cls, name) pair."""
    a1 = get_alias(Entity, "used")
    a2 = get_alias(Entity, "used")
    assert a1 is a2


def test_get_alias_distinctness():
    """get_alias returns different objects for different name arguments."""
    a1 = get_alias(Entity, "used")
    a2 = get_alias(Entity, "generated")
    assert a1 is not a2


def test_get_alias_is_usable_in_queries():
    """get_alias returns an AliasedClass that works in SQLAlchemy select()."""
    alias = get_alias(Entity, "test_query")
    q = sa.select(Entity).join(alias, Entity.id == alias.id)
    compiled = str(q.compile(compile_kwargs={"literal_binds": True}))
    assert "JOIN" in compiled


def test_build_aliases():
    """build_aliases constructs an Aliases dict backed by get_alias singletons."""
    aliases = build_aliases((Entity, "used"), (Entity, "generated"), (BrainRegion, "br"))
    assert Entity in aliases
    assert "used" in aliases[Entity]
    assert "generated" in aliases[Entity]
    assert aliases[Entity]["used"] is get_alias(Entity, "used")
    assert aliases[Entity]["generated"] is get_alias(Entity, "generated")

    assert BrainRegion in aliases
    assert "br" in aliases[BrainRegion]
    assert aliases[BrainRegion]["br"] is get_alias(BrainRegion, "br")


def test_merge_aliases():
    """merge_aliases combines two Aliases dicts."""
    a = build_aliases((Entity, "used"))
    b = build_aliases((Entity, "generated"), (BrainRegion, "br"))
    merged = merge_aliases(a, b)

    assert Entity in merged
    assert "used" in merged[Entity]
    assert "generated" in merged[Entity]

    assert BrainRegion in merged
    assert "br" in merged[BrainRegion]


def test_build_aliases_returns_empty_for_no_pairs():
    """build_aliases with no pairs returns empty dict."""
    aliases = build_aliases()
    assert len(aliases) == 0
