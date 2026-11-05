import re
import uuid
from typing import Annotated, get_args

import pytest
import sqlalchemy as sa
from pydantic import MISSING, AliasPath, Field, ValidationError
from sqlalchemy.orm import joinedload, raiseload

from app.application import app
from app.db.model import CellMorphology, Circuit, Species, Strain
from app.db.types import DerivationType
from app.queries import expand as test_module, expand_loaders
from app.schemas.base import ExpandableSchema, Schema
from app.schemas.cell_morphology import CellMorphologyRead
from app.schemas.circuit import CircuitRead
from app.schemas.expand import Expandable, ExpandLoaderName

DERIVATION_VALUES = {
    "generated_from_derivations",
    "used_by_derivations",
    *(
        f"{direction}:{t}"
        for direction in ("generated_from_derivations", "used_by_derivations")
        for t in DerivationType
    ),
}


class SpeciesTestRead(ExpandableSchema):
    id: uuid.UUID
    name: str
    embedding: Annotated[list[float] | MISSING, Expandable()] = MISSING


class StrainTestRead(Schema):
    """Non-expandable relationship to a schema with an expandable column."""

    id: uuid.UUID
    species: SpeciesTestRead


class StrainExpandableSpeciesTestRead(ExpandableSchema):
    """Expandable relationship, with a validation alias for the ORM attribute."""

    id: uuid.UUID
    expandable_species: Annotated[
        SpeciesTestRead | MISSING, Expandable(), Field(validation_alias="species")
    ] = MISSING


def _strain_query(strain_id):
    return sa.select(Strain).where(Strain.id == strain_id)


def test_allowed_expand_paths():
    assert set(test_module.allowed_expand_paths(CircuitRead, Circuit)) == DERIVATION_VALUES
    assert set(test_module.allowed_expand_paths(CellMorphologyRead, CellMorphology)) == (
        DERIVATION_VALUES | {"measurement_annotation"}
    )
    assert test_module.allowed_expand_paths(StrainTestRead, Strain) == ("species.embedding",)
    assert test_module.allowed_expand_paths(StrainExpandableSpeciesTestRead, Strain) == (
        "expandable_species",
        "expandable_species.embedding",
    )


def test_expand_enum():
    enum = test_module.expand_enum(CircuitRead, Circuit)
    assert enum.__name__ == "CircuitReadExpand"
    assert {str(v) for v in enum} == DERIVATION_VALUES
    assert enum("generated_from_derivations:circuit_extraction").name == (
        "generated_from_derivations__circuit_extraction"
    )
    enum = test_module.expand_enum(StrainExpandableSpeciesTestRead, Strain)
    assert enum("expandable_species.embedding").name == "expandable_species___embedding"


def test_expand_enum_without_expandable_fields():
    class NotExpandableRead(Schema):
        id: uuid.UUID

    with pytest.raises(TypeError, match="no expandable fields"):
        test_module.expand_enum(NotExpandableRead, Strain)


def test_expandable_relationship_to_entities_requires_loader():
    class NestedRead(Schema):
        id: uuid.UUID

    class MorphologyRead(ExpandableSchema):
        id: uuid.UUID
        subject: Annotated[NestedRead | MISSING | None, Expandable()] = MISSING

    with pytest.raises(TypeError, match="require a custom loader"):
        test_module.allowed_expand_paths(MorphologyRead, CellMorphology)


def test_expandable_field_checks():
    with pytest.raises(TypeError, match="must allow and default to MISSING"):

        class DefaultNone(ExpandableSchema):
            summary: Annotated[dict | None, Expandable()] = None

    with pytest.raises(TypeError, match="must allow and default to MISSING"):

        class TypeWithoutMissing(ExpandableSchema):
            summary: Annotated[dict, Expandable()] = MISSING  # pyright: ignore[reportAssignmentType]

    with pytest.raises(TypeError, match="must not allow None"):

        class ListWithNone(ExpandableSchema):
            items: Annotated[list[int] | MISSING | None, Expandable()] = MISSING

    with pytest.raises(TypeError, match="must inherit from ExpandableSchema"):

        class NotExpandableSchema(Schema):
            summary: Annotated[dict | MISSING, Expandable()] = MISSING

    with pytest.raises(TypeError, match="validation_alias of expandable fields must be a string"):

        class AliasPathSchema(ExpandableSchema):
            summary: Annotated[
                dict | MISSING, Expandable(), Field(validation_alias=AliasPath("a", "b"))
            ] = MISSING


def test_collected_orm_attrs():
    assert StrainExpandableSpeciesTestRead.__expandable_fields__["expandable_species"].attr == (
        "species"
    )
    assert SpeciesTestRead.__expandable_fields__["embedding"].attr == "embedding"


def test_collected_loader_names():
    fields = CircuitRead.__expandable_fields__
    assert fields["generated_from_derivations"].loader == "generated_from_derivations"
    assert fields["used_by_derivations"].loader == "used_by_derivations"
    assert SpeciesTestRead.__expandable_fields__["embedding"].loader is None


def test_custom_loaders():
    loaders = expand_loaders.CUSTOM_LOADERS
    assert loaders["generated_from_derivations"].qualifiers == tuple(DerivationType)
    assert loaders["used_by_derivations"].qualifiers == tuple(DerivationType)
    assert loaders["measurement_annotation"].qualifiers == ()


def _schema_subclasses(cls):
    for subclass in cls.__subclasses__():
        yield subclass
        yield from _schema_subclasses(subclass)


def test_custom_loaders_in_sync():
    # the app is imported above, so all the schemas are defined
    used = {
        f.loader
        for cls in _schema_subclasses(Schema)
        for f in cls.__expandable_fields__.values()
        if f.loader is not None
    }
    names = set(get_args(ExpandLoaderName.__value__))
    assert set(expand_loaders.CUSTOM_LOADERS) == names == used


@pytest.mark.parametrize(
    ("expand", "expected"),
    [
        ({"a"}, {"a": None}),
        ({"a:x"}, {"a": frozenset({"x"})}),
        ({"a:x", "a:y"}, {"a": frozenset({"x", "y"})}),
        (["a:x", "a"], {"a": None}),
        (["a", "a:x"], {"a": None}),
        ({"a:x", "b.c"}, {"a": frozenset({"x"}), "b.c": None}),
    ],
)
def test_requested_qualifiers(expand, expected):
    # dict keys keep the order, to check that a value without qualifier wins in any order
    assert test_module._requested_qualifiers(dict.fromkeys(expand).keys()) == expected


def test_nested_column(db, strain_id):
    db.expunge_all()
    query = _strain_query(strain_id).options(joinedload(Strain.species), raiseload("*"))
    strain = db.execute(query).unique().scalar_one()
    assert "embedding" not in StrainTestRead.model_validate(strain).model_dump()["species"]

    db.expunge_all()
    query = test_module.apply_expand(query, Strain, StrainTestRead, {"species.embedding"})
    strain = db.execute(query).unique().scalar_one()
    data = StrainTestRead.model_validate(strain).model_dump()
    assert len(data["species"]["embedding"]) == Species.SIZE


def test_expandable_relationship(db, strain_id):
    db.expunge_all()
    query = _strain_query(strain_id).options(raiseload("*"))
    strain = db.execute(query).unique().scalar_one()
    data = StrainExpandableSpeciesTestRead.model_validate(strain).model_dump()
    assert data.keys() == {"id"}

    db.expunge_all()
    expanded = test_module.apply_expand(
        query, Strain, StrainExpandableSpeciesTestRead, {"expandable_species"}
    )
    strain = db.execute(expanded).unique().scalar_one()
    data = StrainExpandableSpeciesTestRead.model_validate(strain).model_dump()
    assert data["expandable_species"].keys() == {"id", "name"}

    # a nested path implies its expandable ancestors
    db.expunge_all()
    expanded = test_module.apply_expand(
        query, Strain, StrainExpandableSpeciesTestRead, {"expandable_species.embedding"}
    )
    strain = db.execute(expanded).unique().scalar_one()
    data = StrainExpandableSpeciesTestRead.model_validate(strain).model_dump()
    assert data["expandable_species"].keys() == {"id", "name", "embedding"}

    # the options of an ancestor and of a nested path are merged
    db.expunge_all()
    expanded = test_module.apply_expand(
        query,
        Strain,
        StrainExpandableSpeciesTestRead,
        {"expandable_species", "expandable_species.embedding"},
    )
    strain = db.execute(expanded).unique().scalar_one()
    data = StrainExpandableSpeciesTestRead.model_validate(strain).model_dump()
    assert data["expandable_species"].keys() == {"id", "name", "embedding"}


def test_not_expandable_relationship_not_loaded_still_raises(db, strain_id):
    db.expunge_all()
    strain = db.execute(_strain_query(strain_id).options(raiseload("*"))).scalar_one()
    with pytest.raises(ValidationError, match="lazy='raise'"):
        StrainTestRead.model_validate(strain)


@pytest.mark.parametrize(
    "path",
    [
        "species.name",  # not expandable
        "unknown",  # not a schema field
        "species.unknown",
        "species.embedding.x",  # below a column
        "species",  # not expandable relationship, only traversed
    ],
)
def test_invalid_expand_path(path):
    with pytest.raises(ValueError, match=f"Invalid expand path: {re.escape(path)}$"):
        test_module.apply_expand(sa.select(Strain), Strain, StrainTestRead, {path})


def test_expandable_field_without_orm_attribute():
    class StrainSummaryRead(ExpandableSchema):
        id: uuid.UUID
        summary: Annotated[dict | MISSING, Expandable()] = MISSING

    with pytest.raises(TypeError, match="summary: no ORM attribute 'summary' on Strain"):
        test_module.allowed_expand_paths(StrainSummaryRead, Strain)


def test_allowed_expand_paths_not_a_schema():
    with pytest.raises(TypeError, match="is not a Schema"):
        test_module.allowed_expand_paths(int, Strain)  # pyright: ignore[reportArgumentType]


def test_unrequested_loaded_attrs(db, species_id):
    db.expunge_all()
    query = sa.select(Species).where(Species.id == species_id)
    query = test_module.apply_expand(query, Species, SpeciesTestRead, {"embedding"})
    species = db.execute(query).scalar_one()
    assert test_module.unrequested_loaded_attrs(species, SpeciesTestRead, set()) == ["embedding"]
    assert test_module.unrequested_loaded_attrs(species, SpeciesTestRead, {"embedding"}) == []


def test_openapi_expand_param():
    schema = app.openapi()
    components = schema["components"]["schemas"]
    assert set(components["CircuitReadExpand"]["enum"]) == DERIVATION_VALUES
    assert set(components["CellMorphologyReadExpand"]["enum"]) == (
        DERIVATION_VALUES | {"measurement_annotation"}
    )
    for path, method in [
        ("/circuit", "get"),
        ("/circuit", "post"),
        ("/circuit/{id_}", "get"),
        ("/circuit/{id_}", "patch"),
    ]:
        params = {p["name"]: p for p in schema["paths"][path][method]["parameters"]}
        assert params["expand"]["description"] == test_module.EXPAND_DESCRIPTION
        assert params["expand"]["schema"]["anyOf"][0]["items"]["$ref"].endswith(
            "/CircuitReadExpand"
        )
    # the expandable fields are documented and not required
    circuit = components["CircuitRead"]
    assert circuit["properties"]["generated_from_derivations"]["type"] == "array"
    assert "generated_from_derivations" not in circuit["required"]
    morphology = components["CellMorphologyRead"]
    assert "measurement_annotation" in morphology["properties"]
    assert "measurement_annotation" not in morphology["required"]
    assert "CellMorphologyAnnotationExpandedRead" not in components
