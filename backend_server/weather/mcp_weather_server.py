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

Running this module directly:
- From the backend_server directory:
    python weather/mcp_weather_server.py
- Or from the weather directory itself:
    python mcp_weather_server.py
- Or using the module syntax from the backend_server parent:
    python -m weather.mcp_weather_server

Import strategy implemented below:
- Prefer relative import when package context is available (normal Django usage).
- If relative import fails (common when running as a script), we compute the project
  root (backend_server) and insert it into sys.path so that absolute imports like
  `from weather.services import ...` succeed without installing as a package.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Iterable, Optional

# Robust import strategy for dual use (package and script)
# We ensure that the backend_server directory is on sys.path so that
# "weather" can be imported as a top-level package even when this file
# is executed directly (e.g., `python mcp_weather_server.py`).
def _ensure_backend_root_on_path() -> None:
    # __file__ is .../backend_server/weather/mcp_weather_server.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    weather_dir = os.path.dirname(current_dir)                 # .../backend_server/weather
    backend_root = os.path.dirname(weather_dir)                # .../backend_server
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)

# First, try relative import when package context is available
try:
    from .services import WeatherQuery, MockWeatherProvider  # type: ignore
except Exception:
    # If relative import fails (likely when run as a script), fix sys.path and retry absolute import
    _ensure_backend_root_on_path()
    from weather.services import WeatherQuery, MockWeatherProvider  # type: ignore


# PUBLIC_INTERFACE
def serve_weather_stream(city: Optional[str], units: str = "metric", delay_seconds: float = 0.35) -> Iterable[bytes]:
    """Yield a weather stream as ndjson bytes suitable for HTTP chunked streaming.

    Args:
        city: Optional city name.
        units: Unit system ('metric' or 'imperial').
        delay_seconds: Delay between chunks to simulate progressive updates.

    Returns:
        Iterable of bytes chunks. Each chunk is a JSON object plus '\\n'.

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
    # Demonstration entrypoint for running the stream directly from the terminal.
    #
    # This supports multiple invocation patterns without requiring package installation:
    # - From the backend_server directory:
    #       python weather/mcp_weather_server.py
    # - From inside the weather directory:
    #       python mcp_weather_server.py
    # - From the backend_server parent directory (module syntax):
    #       python -m weather.mcp_weather_server
    #
    # You can customize the demo with environment variables:
    #   MCP_WEATHER_CITY (default: "Berlin")
    #   MCP_WEATHER_UNITS (default: "metric")
    demo_city = os.environ.get("MCP_WEATHER_CITY", "Berlin")
    demo_units = os.environ.get("MCP_WEATHER_UNITS", "metric")

    # Emit a short ndjson stream to stdout for quick manual validation.
    for chunk in serve_weather_stream(demo_city, demo_units, delay_seconds=0.05):
        # Chunks are bytes already; write directly to stdout
        sys.stdout.buffer.write(chunk)
        sys.stdout.flush()
