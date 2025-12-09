def convert_to_ilike_pattern(value: str) -> str:
    r"""Convert user input to SQL ILIKE pattern with wildcard support.

    Supports simple wildcard matching where:
    - '*' matches zero or more characters (converted to SQL '%')
    - '?' matches exactly one character (converted to SQL '_')
    - All other characters are escaped to be treated as literals

    SQL metacharacters (%, _, \\) in the input are automatically escaped
    to prevent unintended pattern matching.

    Args:
        value: String with optional wildcards

    Returns:
        SQL ILIKE-compatible pattern string

    Examples:
        >>> convert_to_ilike_pattern("test*")
        "test%"
        >>> convert_to_ilike_pattern("file?.txt")
        "file_.txt"
        >>> convert_to_ilike_pattern("data_file")
        "data\\_file"
        >>> convert_to_ilike_pattern("100% complete")
        "100\\% complete"
    """
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = escaped.replace("*", "%").replace("?", "_")
    return pattern
