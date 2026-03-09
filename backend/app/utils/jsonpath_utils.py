"""JSONPath utilities for API testing.

This module provides JSONPath parsing and extraction utilities.
"""

import json
from typing import Any, List, Optional, Union
from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.ext import parse as jsonpath_ext_parse


class JSONPathError(Exception):
    """Custom exception for JSONPath errors."""
    pass


def extract_json_path(
    json_data: Union[str, dict, list],
    path: str,
    use_extended: bool = True,
) -> List[Any]:
    """Extract values from JSON data using JSONPath expression.

    Args:
        json_data: JSON string or dict/list to query
        path: JSONPath expression (e.g., "$.data.user.name")
        use_extended: If True, use extended JSONPath syntax (default)

    Returns:
        List of matched values (empty list if no matches)

    Raises:
        JSONPathError: If JSONPath expression is invalid
    """
    # Parse JSON string if needed
    if isinstance(json_data, str):
        try:
            json_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise JSONPathError(f"Invalid JSON data: {e}")

    # Parse JSONPath expression
    try:
        if use_extended:
            jsonpath_expr = jsonpath_ext_parse(path)
        else:
            jsonpath_expr = jsonpath_parse(path)
    except Exception as e:
        raise JSONPathError(f"Invalid JSONPath expression '{path}': {e}")

    # Find matches
    try:
        matches = [match.value for match in jsonpath_expr.find(json_data)]
        return matches
    except Exception as e:
        raise JSONPathError(f"Error executing JSONPath '{path}': {e}")


def extract_first(
    json_data: Union[str, dict, list],
    path: str,
    default: Any = None,
    use_extended: bool = True,
) -> Any:
    """Extract first matching value from JSON data.

    Args:
        json_data: JSON string or dict/list to query
        path: JSONPath expression
        default: Default value if no matches found
        use_extended: If True, use extended JSONPath syntax

    Returns:
        First matched value or default
    """
    try:
        matches = extract_json_path(json_data, path, use_extended)
        return matches[0] if matches else default
    except JSONPathError:
        return default


def exists_at_path(
    json_data: Union[str, dict, list],
    path: str,
    use_extended: bool = True,
) -> bool:
    """Check if a path exists in JSON data.

    Args:
        json_data: JSON string or dict/list to query
        path: JSONPath expression
        use_extended: If True, use extended JSONPath syntax

    Returns:
        True if path has at least one match, False otherwise
    """
    try:
        matches = extract_json_path(json_data, path, use_extended)
        return len(matches) > 0
    except JSONPathError:
        return False


def matches_path_value(
    json_data: Union[str, dict, list],
    path: str,
    expected_value: Any,
    use_extended: bool = True,
) -> bool:
    """Check if value at path matches expected value.

    Args:
        json_data: JSON string or dict/list to query
        path: JSONPath expression
        expected_value: Expected value to match
        use_extended: If True, use extended JSONPath syntax

    Returns:
        True if first match equals expected value
    """
    actual = extract_first(json_data, path, use_extended=use_extended)
    return actual == expected_value
