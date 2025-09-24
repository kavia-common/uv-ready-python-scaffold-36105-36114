"""
MCP stdio server for basic arithmetic operations (addition and subtraction).

This module implements a minimal Model Context Protocol (MCP)-style server that
communicates over standard input/output (stdio). The server reads newline-delimited
JSON requests from stdin, executes the requested operation, and writes a JSON
response to stdout followed by a newline.

Interface specification (stdio JSON protocol):
- Request (newline-delimited JSON per line):
    {
        "id": "<string|number>",            # Optional but recommended for correlating responses
        "operation": "add" | "subtract",    # Required
        "operands": [<number|string>, <number|string>]  # Required, exactly 2 operands
    }

- Response (newline-delimited JSON per line):
    Success:
    {
        "id": "<echoed id or null>",
        "ok": true,
        "result": <number>
    }

    Error:
    {
        "id": "<echoed id or null>",
        "ok": false,
        "error": {
            "code": "<BadRequest|InvalidOperation|InvalidOperands|InternalError>",
            "message": "<human friendly message>"
        }
    }

Behavior and notes:
- Each input line is treated as an independent JSON request.
- Non-JSON or malformed requests return an "BadRequest" error.
- "operation" must be "add" or "subtract".
- "operands" must be a list with exactly 2 items that can be interpreted
  as numbers (int or float). Numeric strings are accepted.
- Responses are always a single JSON object followed by a newline.
- The server continues processing until EOF on stdin.

Usage:
    python mcp_server.py
  Then send newline-delimited JSON via stdin. Example:
    echo '{"id":1,"operation":"add","operands":[2,3]}' | python mcp_server.py

Environment/Dependencies:
- Pure Python, no external dependencies.
- No configuration via environment variables required.

This file also exposes add and subtract as public utility functions so they can
be reused within the Django project if desired.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional, Union

Number = Union[int, float]


def _to_number(value: Any) -> Number:
    """
    Internal helper to convert input to a number (int or float).
    Raises ValueError if conversion fails.
    """
    if isinstance(value, (int, float)):
        return value
    try:
        if isinstance(value, str):
            s = value.strip()
            # Handle integers (including negative)
            if s and (s.isdigit() or (s[0] in "+-" and s[1:].isdigit())):
                return int(s)
            # Fallback to float
            return float(s)
        # Fallback: attempt float conversion for other simple types
        return float(value)  # type: ignore[arg-type]
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


def _make_error_response(req_id: Optional[Union[str, int]], code: str, message: str) -> Dict[str, Any]:
    """Create a standardized error response object."""
    return {
        "id": req_id,
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
    }


def _make_success_response(req_id: Optional[Union[str, int]], result: Number) -> Dict[str, Any]:
    """Create a standardized success response object."""
    return {
        "id": req_id,
        "ok": True,
        "result": result,
    }


def _process_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single request payload and return the response object.

    Expected payload fields:
      - id: optional
      - operation: 'add' or 'subtract'
      - operands: list of exactly 2 values
    """
    req_id = payload.get("id", None)

    # Validate payload structure
    if not isinstance(payload, dict):
        return _make_error_response(req_id, "BadRequest", "Request must be a JSON object.")

    operation = payload.get("operation")
    operands = payload.get("operands")

    if operation not in ("add", "subtract"):
        return _make_error_response(req_id, "InvalidOperation", "Operation must be 'add' or 'subtract'.")

    if not isinstance(operands, list) or len(operands) != 2:
        return _make_error_response(req_id, "InvalidOperands", "Operands must be a list of exactly two items.")

    try:
        a, b = operands[0], operands[1]
        if operation == "add":
            result = add(a, b)
        else:
            result = subtract(a, b)
        return _make_success_response(req_id, result)
    except ValueError as ve:
        return _make_error_response(req_id, "InvalidOperands", str(ve))
    except Exception as exc:  # Catch-all to avoid crashing the server
        return _make_error_response(req_id, "InternalError", f"Unexpected error: {exc}")


# PUBLIC_INTERFACE
def serve_stdio() -> None:
    """Run the MCP stdio server loop.

    Reads newline-delimited JSON objects from stdin, processes each request,
    and writes a JSON response followed by a newline to stdout.

    Protocol details:
      - One JSON object per line for requests and responses.
      - See module docstring for request/response format.
      - Continues until EOF is reached on stdin.

    This function is intended to be used as the main entry point when running
    this module as a script.
    """
    # Use sys.stdin to iterate line by line until EOF
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            # Ignore empty lines to be tolerant
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as jde:
            resp = _make_error_response(None, "BadRequest", f"Invalid JSON: {jde.msg}")
        else:
            if not isinstance(payload, dict):
                resp = _make_error_response(payload.get("id") if isinstance(payload, dict) else None,
                                            "BadRequest", "Top-level JSON must be an object.")
            else:
                resp = _process_request(payload)

        # Always emit a single-line JSON response
        sys.stdout.write(json.dumps(resp, separators=(",", ":")) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    # When executed directly, start the stdio server.
    serve_stdio()
