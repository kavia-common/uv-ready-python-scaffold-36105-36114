"""
Weather app package for streamable weather info services and an MCP-style HTTP server.

This app provides:
- A Django REST endpoint that streams weather information using StreamingHttpResponse.
- A modular service layer (weather/services.py) intended for future integration with external APIs.
- An MCP-style HTTP server module (weather/mcp_weather_server.py) that demonstrates
  streamable HTTP transport semantics by yielding chunked JSON lines.

The module is designed to be extended without changing public contracts.
"""
