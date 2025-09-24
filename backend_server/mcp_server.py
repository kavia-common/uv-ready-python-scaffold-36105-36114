"""
Lightweight MCP server utilities for basic arithmetic operations.

This module provides simple functions to perform addition and subtraction.
These can be imported and used anywhere within the Django project (e.g., views,
management commands, or other services).

Design notes:
- Kept as a standalone utility module at the backend_server root to reflect a
  project-level MCP-like service. This avoids tight coupling with the `api` app.
- Public interfaces are documented and annotated for clarity.
- Input validation ensures values can be interpreted as numbers.
"""

from typing import Union


Number = Union[int, float]


def _to_number(value) -> Number:
    """
    Internal helper to convert input to a number (int or float).
    Raises ValueError if conversion fails.
    """
    # Allow direct int/float
    if isinstance(value, (int, float)):
        return value
    # Try to parse common string representations
    try:
        # First try int to preserve integer arithmetic where possible
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
        # Fallback to float conversion
        return float(value)  # May raise ValueError
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Unable to interpret value '{value}' as a number.") from exc


# PUBLIC_INTERFACE
def add(a: Union[Number, str], b: Union[Number, str]) -> Number:
    """Return the arithmetic sum of a and b.

    Args:
        a: First addend. Can be int, float, or numeric string.
        b: Second addend. Can be int, float, or numeric string.

    Returns:
        The sum of a and b, as int if both are ints, otherwise float.

    Raises:
        ValueError: If either value cannot be interpreted as a number.
    """
    na = _to_number(a)
    nb = _to_number(b)
    return na + nb


# PUBLIC_INTERFACE
def subtract(a: Union[Number, str], b: Union[Number, str]) -> Number:
    """Return the arithmetic difference a - b.

    Args:
        a: Minuend. Can be int, float, or numeric string.
        b: Subtrahend. Can be int, float, or numeric string.

    Returns:
        The difference a - b, as int if both are ints, otherwise float.

    Raises:
        ValueError: If either value cannot be interpreted as a number.
    """
    na = _to_number(a)
    nb = _to_number(b)
    return na - nb
