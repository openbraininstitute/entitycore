import re
from typing import Annotated

from pydantic import AfterValidator

ORCID_REGEX = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{4}$")
ROR_REGEX = re.compile(r"^0[a-z0-9]{8}$")


def validate_orcid(value: str) -> str:
    if value is None:
        return value

    value = value.strip()

    # normalize URI form
    if value.startswith("https://orcid.org/"):
        value = value.rsplit("/", 1)[-1]

    if not ORCID_REGEX.match(value):
        msg = f"Invalid ORCID: {value}"
        raise ValueError(msg)

    return value


ORCID = Annotated[str, AfterValidator(validate_orcid)]


def validate_ror(value: str) -> str:
    if value is None:
        return value

    value = value.strip().lower()

    # normalize URL form
    if value.startswith("https://ror.org/"):
        value = value.rsplit("/", 1)[-1]

    if not ROR_REGEX.match(value):
        msg = f"Invalid ROR ID: {value}"
        raise ValueError(msg)

    return value


ROR_ID = Annotated[str, AfterValidator(validate_ror)]
