import re
from typing import Annotated

from pydantic import AfterValidator

ORCID_URL_PREFIX = "https://orcid.org/"
ROR_URL_PREFIX = "https://ror.org/"

ORCID_REGEX = re.compile(rf"^{re.escape(ORCID_URL_PREFIX)}\d{{4}}-\d{{4}}-\d{{4}}-\d{{3}}[\dXx]$")
ROR_CROCKFORD_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
ROR_CROCKFORD_VALUES = {ch: index for index, ch in enumerate(ROR_CROCKFORD_ALPHABET)}
ROR_REGEX = re.compile(rf"^{re.escape(ROR_URL_PREFIX)}0[a-hj-km-np-tv-z0-9]{{6}}[0-9]{{2}}$")


def _is_orcid_valid_checksum(value: str) -> str:
    """Generate check digit as per ISO 7064 11,2.

    See: https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier
    """
    value = value[len(ORCID_URL_PREFIX) :].replace("-", "")

    base_digits = value[:-1]
    expected_checksum = int(value[-1]) if value[-1] != "X" else 10

    total = 0
    for ch in base_digits:
        total = (total + int(ch)) * 2

    remainder = total % 11
    result = (12 - remainder) % 11

    return result == expected_checksum


def validate_orcid(value: str) -> str:
    if value is None:
        return value

    value = value.strip()

    if not ORCID_REGEX.match(value):
        msg = f"Invalid ORCID: {value}"
        raise ValueError(msg)

    # normalize last x -> X
    if value[-1] == "x":
        value = f"{value[:-1]}X"

    if not _is_orcid_valid_checksum(value):
        msg = f"Invalid ORCID checksum: {value}"
        raise ValueError(msg)

    return value


ORCID = Annotated[str, AfterValidator(validate_orcid)]


def _is_ror_valid_checksum(value: str) -> bool:
    # https://github.com/ror-community/ror-api/blob/bd040a0d2558a478c06a89118a29eeb9b6142710/rorapi/management/commands/generaterorid.py#L17
    # https://github.com/jbittel/base32-crockford/blob/1ffb6021485b666ea6a562abd0a1ea6f7021188f/base32_crockford.py#L59

    ror_id = value[len(ROR_URL_PREFIX) :]

    base, check = ror_id[:7], ror_id[7:]
    encoded = 0
    for ch in base:
        encoded = encoded * 32 + ROR_CROCKFORD_VALUES[ch]

    remainder = 0
    for ch in f"{encoded}{check}":
        remainder = (remainder * 10 + int(ch)) % 97

    return remainder == 1


def validate_ror(value: str) -> str:

    value = value.strip().lower()

    if not ROR_REGEX.match(value):
        msg = f"Invalid ROR ID: {value}"
        raise ValueError(msg)

    if not _is_ror_valid_checksum(value):
        msg = f"Invalid ROR ID checksum: {value}"
        raise ValueError(msg)

    return value


ROR_ID = Annotated[str, AfterValidator(validate_ror)]
