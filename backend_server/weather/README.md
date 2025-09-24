# Weather MCP Server (HTTP Streaming)

Overview
- Provides a standalone weather component with an MCP-style, streamable HTTP interface.
- Demonstrates using Django's StreamingHttpResponse to deliver newline-delimited JSON (ndjson) chunks.
- Ready for future integration with external weather APIs via the service abstraction.

Endpoints
- GET /weather/mcp-usage/  
  Returns guidance on how to use the streaming endpoint and pointers to API docs.
- GET /weather/stream/?city=Berlin&units=metric  
  Streams ndjson chunks:
  1) header line (metadata)
  2) multiple update lines (partial results)
  3) trailer line (done flag)

Streaming Format
- Content-Type: application/x-ndjson
- Each line is a complete JSON object terminated by \n. Clients can parse line by line.

Client Usage Tips
- Prefer a streaming HTTP client that does not buffer the entire body.
- Read the response incrementally and parse each line as JSON.

Extending with a Real Weather Provider
- Implement WeatherProvider with a concrete class that calls a third-party API.
- Use environment variables (e.g., WEATHER_API_KEY, WEATHER_API_URL) configured in .env
  and injected into settings. Do not hardcode secrets.
- Replace MockWeatherProvider in views/mcp server with the real provider.
