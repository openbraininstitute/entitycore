"""Unit tests for pydantic ORCID and ROR ID validators."""

import pytest
from pydantic import TypeAdapter, ValidationError

from app.utils import pydantic_validators as test_module

ORCIDAdapter = TypeAdapter(test_module.ORCID)
RORAdapter = TypeAdapter(test_module.ROR_ID)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://orcid.org/0000-0001-2345-6789", "https://orcid.org/0000-0001-2345-6789"),
        ("  https://orcid.org/0000-0001-2345-6789  ", "https://orcid.org/0000-0001-2345-6789"),
        ("https://orcid.org/0000-0003-1234-5674", "https://orcid.org/0000-0003-1234-5674"),
        ("https://orcid.org/0000-0001-1111-110x", "https://orcid.org/0000-0001-1111-110X"),
    ],
)
def test_validate_orcid__valid(value: str, expected: str) -> None:
    assert test_module.validate_orcid(value) == expected
    assert ORCIDAdapter.validate_python(value) == expected


def test_validate_orcid__none() -> None:
    assert test_module.validate_orcid(None) is None


@pytest.mark.parametrize(
    "value",
    [
        "https://orcid.org/0000-0001-2345-6789",
        "https://orcid.org/0000-0003-1234-5674",
        "https://orcid.org/0000-0002-1825-0097",
        "https://orcid.org/0000-0001-1111-110X",
        "https://orcid.org/0000-0002-1694-233X",
        "https://orcid.org/0000-0001-5109-3700",
    ],
)
def test_is_orcid_valid_checksum__valid(value: str) -> None:
    assert test_module._is_orcid_valid_checksum(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "https://orcid.org/0000-0003-1234-5678",
        "https://orcid.org/0000-0001-2345-6780",
        "https://orcid.org/0000-0001-2345-6781",
    ],
)
def test_is_orcid_valid_checksum__invalid(value: str) -> None:
    assert test_module._is_orcid_valid_checksum(value) is False


@pytest.mark.parametrize(
    "value",
    [
        "https://orcid.org/0000-0003-1234-5678",
        "https://orcid.org/0000-0001-2345-6780",
        "https://orcid.org/0000-0001-2345-6781",
        "https://orcid.org/0000-0001-2345-678X",
    ],
)
def test_validate_orcid__invalid_checksum(value: str) -> None:
    with pytest.raises(ValueError, match="Invalid ORCID checksum:"):
        test_module.validate_orcid(value)

    with pytest.raises(ValidationError):
        ORCIDAdapter.validate_python(value)


@pytest.mark.parametrize(
    "value",
    [
        "https://orcid.org/invalid-orcid",
        "https://orcid.org/0000-0001-234",
        "https://orcid.org/0000-0001-2345-67890",
        "https://orcid.org/abcd-0001-2345-6789",
    ],
)
def test_validate_orcid__invalid(value: str) -> None:
    with pytest.raises(ValueError, match="Invalid ORCID:"):
        test_module.validate_orcid(value)

    with pytest.raises(ValidationError):
        ORCIDAdapter.validate_python(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://ror.org/02rx3b187", "https://ror.org/02rx3b187"),
        ("  https://ROR.org/02RX3B187  ", "https://ror.org/02rx3b187"),
        ("https://ror.org/01an7q238", "https://ror.org/01an7q238"),
    ],
)
def test_validate_ror__valid(value: str, expected: str) -> None:
    assert test_module.validate_ror(value) == expected
    assert RORAdapter.validate_python(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "https://ror.org/02rx3b187",
        "https://ror.org/02mhbdp94",
        "https://ror.org/01an7q238",
        "https://ror.org/03sf5ja42",
        "https://ror.org/00ddy0v87",
    ],
)
def test_is_ror_valid_checksum__valid(value: str) -> None:
    assert test_module._is_ror_valid_checksum(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "https://ror.org/04wx1j267",
        "https://ror.org/03nawhv71",
        "https://ror.org/02rx3b180",
    ],
)
def test_is_ror_valid_checksum__invalid(value: str) -> None:
    assert test_module._is_ror_valid_checksum(value) is False


@pytest.mark.parametrize(
    "value",
    [
        "https://ror.org/04wx1j267",
        "https://ror.org/02rx3b180",
    ],
)
def test_validate_ror__invalid_checksum(value: str) -> None:
    with pytest.raises(ValueError, match="Invalid ROR ID checksum:"):
        test_module.validate_ror(value)

    with pytest.raises(ValidationError):
        RORAdapter.validate_python(value)


@pytest.mark.parametrize(
    "value",
    [
        "https://ror.org/invalid-ror",
        "https://ror.org/02rx3b18",
        "https://ror.org/02mhbdp9_1",
        "https://ror.org/12rx3b187",
        "https://ror.org/02rx3i187",
        "https://ror.org/02lrx3b18",
        "https://ror.org/02abc",
    ],
)
def test_validate_ror__invalid(value: str) -> None:
    with pytest.raises(ValueError, match="Invalid ROR ID:"):
        test_module.validate_ror(value)

    with pytest.raises(ValidationError):
        RORAdapter.validate_python(value)
