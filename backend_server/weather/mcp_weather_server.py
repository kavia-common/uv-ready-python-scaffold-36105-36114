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
import time
from typing import Iterable, Optional

from .services import WeatherQuery, MockWeatherProvider


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
