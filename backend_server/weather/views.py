from __future__ import annotations

import json
import time
from typing import Iterable, Optional

from django.http import StreamingHttpResponse, HttpRequest, HttpResponse
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from .services import WeatherQuery, MockWeatherProvider


def _weather_stream_generator(
    city: Optional[str],
    units: str,
    delay_seconds: float = 0.35,
) -> Iterable[bytes]:
    """
    Internal generator that yields bytes chunks representing a stream of weather updates.

    The stream format is "ndjson" (newline-delimited JSON):
    - Each chunk is a single JSON object followed by a newline.
    - First chunk is a lightweight header with request metadata.
    - Subsequent chunks simulate partial updates from a downstream weather API.
    - Final chunk contains a 'done' flag.

    This structure makes it easy for clients to parse incrementally while receiving
    progressive updates over the same HTTP connection.
    """
    provider = MockWeatherProvider()
    query = WeatherQuery(city=city or "Unknown", units=units)

    # Stream header
    header = {
        "type": "header",
        "city": query.city,
        "units": query.units,
        "protocol": "mcp-http-stream",
        "note": "This endpoint uses HTTP chunked transfer via Django StreamingHttpResponse with ndjson.",
    }
    yield (json.dumps(header) + "\n").encode("utf-8")
    time.sleep(delay_seconds)

    # Simulated progressive updates
    for idx, update in enumerate(provider.progressive_forecast(query), start=1):
        chunk = {
            "type": "update",
            "seq": idx,
            "data": update,
        }
        yield (json.dumps(chunk) + "\n").encode("utf-8")
        time.sleep(delay_seconds)

    # Stream trailer
    trailer = {
        "type": "trailer",
        "done": True,
        "message": "Streaming complete",
    }
    yield (json.dumps(trailer) + "\n").encode("utf-8")


# PUBLIC_INTERFACE
@api_view(["GET"])
@renderer_classes([JSONRenderer])
def mcp_weather_usage(request: HttpRequest) -> Response:
    """
    MCP Weather Server - HTTP Streaming Usage Help

    Summary:
        Returns a small JSON object describing how to use the streamable weather endpoint.

    Query Parameters:
        - city (optional): City name for the weather lookup.
        - units (optional): 'metric' or 'imperial'. Default: 'metric'.

    Returns:
        200 OK JSON with 'endpoints' and 'notes' fields explaining client usage.

    Notes:
        - The stream endpoint streams newline-delimited JSON (ndjson).
        - Clients should read the response as a stream and parse JSON lines as they arrive.
    """
    base = request.build_absolute_uri("/")
    stream_url = request.build_absolute_uri("/weather/stream/")
    data = {
        "endpoints": {
            "stream_weather": stream_url + "?city=Berlin&units=metric",
        },
        "notes": [
            "This server uses Django StreamingHttpResponse to send chunked ndjson.",
            "Consume the response incrementally; do not buffer the entire body.",
            "Each line is a self-contained JSON object.",
        ],
        "docs": base + "docs/",
        "openapi": base + "swagger.json",
    }
    return Response(data)


# PUBLIC_INTERFACE
def stream_weather(request: HttpRequest) -> HttpResponse:
    """
    Weather Stream (HTTP chunked, ndjson)

    Summary:
        Streams weather-like updates over a single HTTP connection.

    Query Parameters:
        - city: Optional; city name to query (string).
        - units: Optional; 'metric' (default) or 'imperial'.

    Returns:
        StreamingHttpResponse with 'application/x-ndjson' content type.
        The body is a sequence of lines, each a JSON object terminated by '\n'.

    Usage:
        GET /weather/stream/?city=Berlin&units=metric
        Client should read the response stream line by line and parse JSON per line.

    Implementation details:
        Uses Django's StreamingHttpResponse which employs chunked transfer encoding
        when supported by the server stack. This is suitable for MCP-style
        streamable HTTP transport semantics.
    """
    city = request.GET.get("city")
    units = request.GET.get("units", "metric")
    generator = _weather_stream_generator(city=city, units=units)
    response = StreamingHttpResponse(
        streaming_content=generator, content_type="application/x-ndjson"
    )
    response["Cache-Control"] = "no-store"
    response["X-MCP-Transport"] = "http-stream"
    return response
