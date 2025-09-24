from django.urls import path
from .views import stream_weather, mcp_weather_usage

urlpatterns = [
    path("stream/", stream_weather, name="weather_stream"),
    path("mcp-usage/", mcp_weather_usage, name="weather_mcp_usage"),
]
