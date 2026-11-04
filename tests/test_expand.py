import pytest

from app.application import app
from app.db.types import DerivationType
from app.queries import expand as test_module

GENERATED = test_module.DerivationExpandDirection.generated_from_derivations
USED = test_module.DerivationExpandDirection.used_by_derivations
EXTRACTION = DerivationType.circuit_extraction
REWIRING = DerivationType.circuit_rewiring


def test_entity_expand_values():
    expected = {
        "generated_from_derivations",
        "used_by_derivations",
        *(
            f"{direction}:{t}"
            for direction in ("generated_from_derivations", "used_by_derivations")
            for t in DerivationType
        ),
    }
    assert {str(v) for v in test_module.EntityExpand} == expected
    assert len(expected) == 2 + 2 * len(DerivationType)
    assert test_module.EntityExpand("generated_from_derivations:circuit_extraction").name == (
        "generated_from_derivations__circuit_extraction"
    )
    assert {str(v) for v in test_module.MeasurableEntityExpand} == expected | {
        test_module.MEASUREMENT_ANNOTATION_EXPAND
    }


def test_build_expand_enum_extra_values():
    enum = test_module._build_expand_enum("MyExpand", extra_values=["foo"])
    assert enum.__name__ == "MyExpand"
    assert "foo" in enum
    assert "generated_from_derivations.used" not in enum


@pytest.mark.parametrize(
    ("expand", "expected"),
    [
        (None, {}),
        (set(), {}),
        ({test_module.MEASUREMENT_ANNOTATION_EXPAND}, {}),
        ({"generated_from_derivations"}, {GENERATED: None}),
        ({"generated_from_derivations:circuit_extraction"}, {GENERATED: frozenset({EXTRACTION})}),
        (
            {
                "generated_from_derivations:circuit_extraction",
                "generated_from_derivations:circuit_rewiring",
            },
            {GENERATED: frozenset({EXTRACTION, REWIRING})},
        ),
        (
            {"generated_from_derivations:circuit_extraction", "generated_from_derivations"},
            {GENERATED: None},
        ),
        (
            {"used_by_derivations:circuit_rewiring", "generated_from_derivations"},
            {GENERATED: None, USED: frozenset({REWIRING})},
        ),
    ],
)
def test_parse_derivation_expand(expand, expected):
    assert test_module._parse_derivation_expand(expand) == expected


def test_parse_derivation_expand_bare_wins_in_any_order():
    # dicts preserve the insertion order, so both orders are exercised deterministically
    for values in (
        ["generated_from_derivations", "generated_from_derivations:circuit_extraction"],
        ["generated_from_derivations:circuit_extraction", "generated_from_derivations"],
    ):
        result = test_module._parse_derivation_expand(dict.fromkeys(values).keys())
        assert result == {GENERATED: None}


def test_openapi_expand_param():
    schema = app.openapi()
    assert set(schema["components"]["schemas"]["EntityExpand"]["enum"]) == {
        str(v) for v in test_module.EntityExpand
    }
    params = {p["name"]: p for p in schema["paths"]["/circuit"]["get"]["parameters"]}
    assert params["expand"]["description"] == test_module.EXPAND_DESCRIPTION
    params = {p["name"]: p for p in schema["paths"]["/cell-morphology/{id_}"]["get"]["parameters"]}
    assert params["expand"]["schema"]["anyOf"][0]["items"]["$ref"].endswith(
        "/MeasurableEntityExpand"
    )
