"""
MCP-style Weather Server (HTTP streamable transport)

This module exposes a simple Django view-free streaming interface to be mounted
on a URL path. It demonstrates how an MCP server could stream results over HTTP
using newline-delimited JSON (ndjson), enabling incremental consumption by clients.

Public Interface:
- serve_weather_stream(city, units): generator yielding bytes chunks suitable for
  a StreamingHttpResponse's streaming_content.

Notes on streaming HTTP:
- Django's StreamingHttpResponse sends chunks as they are yielded by the generator.
- Upstream servers that support chunked transfer (e.g., gunicorn/uvicorn/ASGI stack)
  will deliver data to clients as it becomes available, without buffering the full body.
- Each chunk is a single JSON object followed by a newline.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Iterable, Optional

# Allow running this module both:
# - as part of the Django package (relative import), and
# - directly via: python mcp_weather_server.py (absolute import fallback).
try:
    from .services import WeatherQuery, MockWeatherProvider  # type: ignore
except ImportError:
    # When executed directly, __package__ is None and relative import fails.
    # Insert the backend_server directory to sys.path and try absolute import.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)
    from weather.services import WeatherQuery, MockWeatherProvider  # type: ignore


# PUBLIC_INTERFACE
def serve_weather_stream(city: Optional[str], units: str = "metric", delay_seconds: float = 0.35) -> Iterable[bytes]:
    """Yield a weather stream as ndjson bytes suitable for HTTP chunked streaming.

    Args:
        city: Optional city name.
        units: Unit system ('metric' or 'imperial').
        delay_seconds: Delay between chunks to simulate progressive updates.

    Returns:
        Iterable of bytes chunks. Each chunk is a JSON object plus '\n'.

    Usage example (inside a Django view):
        from django.http import StreamingHttpResponse
        from weather.mcp_weather_server import serve_weather_stream

        def my_view(request):
            gen = serve_weather_stream(request.GET.get("city"), request.GET.get("units", "metric"))
            return StreamingHttpResponse(gen, content_type="application/x-ndjson")
    """
    provider = MockWeatherProvider()
    query = WeatherQuery(city=city or "Unknown", units=units)

    header = {"type": "mcp_header", "city": query.city, "units": query.units}
    yield (json.dumps(header) + "\n").encode("utf-8")
    time.sleep(delay_seconds)

    for idx, item in enumerate(provider.progressive_forecast(query), start=1):
        yield (json.dumps({"type": "mcp_update", "seq": idx, "data": item}) + "\n").encode("utf-8")
        time.sleep(delay_seconds)

    yield (json.dumps({"type": "mcp_trailer", "done": True}) + "\n").encode("utf-8")


if __name__ == "__main__":
    # If run directly, demonstrate usage by printing a short sample stream to stdout.
    # This allows quick manual testing: python mcp_weather_server.py
    # It will emit a few ndjson lines and exit.
    demo_city = os.environ.get("MCP_WEATHER_CITY", "Berlin")
    demo_units = os.environ.get("MCP_WEATHER_UNITS", "metric")
    for chunk in serve_weather_stream(demo_city, demo_units, delay_seconds=0.05):
        # Chunks are bytes already; write directly to stdout
        sys.stdout.buffer.write(chunk)
        sys.stdout.flush()
