def is_ascii(s: str) -> bool:
    """Return True if a string can be encoded as ASCII."""
    try:
        s.encode("ascii")
    except UnicodeEncodeError:
        return False
    return True


def clip(x: int, min_value: int, max_value: int) -> int:
    """Clip x to the inclusive range [min_value, max_value]."""
    return max(min_value, min(x, max_value))
