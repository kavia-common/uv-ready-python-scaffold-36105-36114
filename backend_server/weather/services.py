from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Generator, Iterable, List


@dataclass(frozen=True)
class WeatherQuery:
    """Container for weather query parameters."""
    city: str
    units: str = "metric"  # 'metric' or 'imperial'


class WeatherProvider:
    """
    Abstract weather provider interface. Implementations can call external APIs.

    For future integration:
    - Implement fetch_current and progressive_forecast using a real weather API.
    - Read API keys and endpoints via environment variables (do not hardcode).
    """

    # PUBLIC_INTERFACE
    def fetch_current(self, query: WeatherQuery) -> Dict:
        """Return current weather for the given query."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def progressive_forecast(self, query: WeatherQuery) -> Iterable[Dict]:
        """
        Yield partial forecast updates progressively.

        Implementations should yield multiple dictionaries that represent
        incremental updates, suitable for streamed delivery.
        """
        raise NotImplementedError


class MockWeatherProvider(WeatherProvider):
    """
    Mock provider returning deterministic data for demonstration/testing and streaming.

    This class simulates:
    - A quick "current" snapshot.
    - A series of partial forecast updates for streaming scenarios.
    """

    def fetch_current(self, query: WeatherQuery) -> Dict:
        temp = 21 if query.units == "metric" else 70
        return {
            "city": query.city,
            "units": query.units,
            "temperature": temp,
            "conditions": "Partly Cloudy",
        }

    def progressive_forecast(self, query: WeatherQuery) -> Generator[Dict, None, None]:
        # In a real provider, each yield might be a page/chunk from an external API.
        base_temp = 21 if query.units == "metric" else 70
        steps: List[Dict] = [
            {"period": "now", "temp": base_temp, "conditions": "Partly Cloudy"},
            {"period": "+1h", "temp": base_temp + 1, "conditions": "Partly Cloudy"},
            {"period": "+2h", "temp": base_temp + 2, "conditions": "Mostly Sunny"},
            {"period": "+3h", "temp": base_temp + 1, "conditions": "Breezy"},
        ]
        for s in steps:
            yield {
                "city": query.city,
                "units": query.units,
                **s,
            }
