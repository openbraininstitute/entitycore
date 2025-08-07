import re

DOI_REGEX = re.compile(r"^10.\d{4,9}\/[-._;()\/:A-Z0-9]+$", re.IGNORECASE)


def is_doi(value: str) -> bool:
    """Verify if the given string is a doi identifier."""
    return bool(DOI_REGEX.match(value))
