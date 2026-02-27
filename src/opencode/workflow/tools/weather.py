"""
Weather Tool

Integration with weather APIs for fetching weather data.
"""

import logging
from typing import Any, Dict, List, Optional, ClassVar

import httpx

from opencode.workflow.tools.registry import BaseTool, ToolResult, ToolSchema, ToolRegistry

logger = logging.getLogger(__name__)


@ToolRegistry.register("weather")
class WeatherTool(BaseTool):
    """
    Weather Tool - Fetch weather data for locations.
    
    This tool provides weather data fetching capabilities using
    Open-Meteo API (free, no API key required) or OpenWeatherMap
    (requires API key for extended features).
    
    Configuration:
        api_key: OpenWeatherMap API key (optional, for extended features)
        units: Temperature units - "celsius" or "fahrenheit" (default: "celsius")
        timeout: Request timeout in seconds (default: 30)
    
    Example:
        tool = WeatherTool()
        result = await tool.execute({"location": "Toronto, Canada"})
        if result.success:
            print(result.data["current"]["temperature"])
    """
    
    _schema = ToolSchema(
        name="weather",
        description="Fetch current weather and forecast for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location name or coordinates (e.g., 'Toronto, Canada' or '43.65,-79.38')",
                },
                "units": {
                    "type": "string",
                    "description": "Temperature units",
                    "enum": ["celsius", "fahrenheit"],
                    "default": "celsius",
                },
                "include_forecast": {
                    "type": "boolean",
                    "description": "Include forecast data",
                    "default": False,
                },
                "forecast_days": {
                    "type": "integer",
                    "description": "Number of forecast days (1-16)",
                    "default": 7,
                },
            },
        },
        required_params=["location"],
        returns="object",
        category="data",
        requires_auth=False,
    )
    
    # Open-Meteo API (free, no API key required)
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    
    @classmethod
    def get_schema(cls) -> ToolSchema:
        """Return the schema for this tool."""
        return cls._schema
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        Fetch weather data for a location.
        
        Args:
            params: Dictionary containing:
                - location: Location name or coordinates (required)
                - units: Temperature units
                - include_forecast: Include forecast data
                - forecast_days: Number of forecast days
            
        Returns:
            ToolResult with weather data
        """
        location = params.get("location")
        if not location:
            return ToolResult(
                success=False,
                error="Required parameter 'location' is missing",
            )
        
        units = params.get("units", self.config.get("units", "celsius"))
        include_forecast = params.get("include_forecast", False)
        forecast_days = params.get("forecast_days", 7)
        timeout = self.config.get("timeout", 30)
        
        try:
            # Geocode location to coordinates
            coords = await self._geocode(location, timeout)
            if not coords:
                return ToolResult(
                    success=False,
                    error=f"Could not find location: {location}",
                )
            
            # Fetch weather data
            weather_data = await self._fetch_weather(
                coords["latitude"],
                coords["longitude"],
                units,
                include_forecast,
                forecast_days,
                timeout,
            )
            
            return ToolResult(
                success=True,
                data={
                    "location": {
                        "name": coords["name"],
                        "country": coords.get("country", ""),
                        "latitude": coords["latitude"],
                        "longitude": coords["longitude"],
                    },
                    "current": weather_data["current"],
                    "forecast": weather_data.get("forecast"),
                    "units": units,
                },
                metadata={
                    "source": "open-meteo",
                },
            )
            
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                error="Weather API request timed out",
            )
        except Exception as e:
            logger.exception(f"Weather fetch error: {e}")
            return ToolResult(
                success=False,
                error=f"Weather fetch failed: {str(e)}",
            )
    
    async def _geocode(self, location: str, timeout: float) -> Optional[Dict[str, Any]]:
        """
        Convert location name to coordinates.
        
        Args:
            location: Location name
            timeout: Request timeout
            
        Returns:
            Dictionary with coordinates and location info
        """
        # Check if location is already coordinates
        if "," in location:
            parts = location.split(",")
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                return {
                    "name": f"{lat}, {lon}",
                    "latitude": lat,
                    "longitude": lon,
                }
            except ValueError:
                pass
        
        params = {
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json",
        }
        
        headers = {
            "User-Agent": "OpenCode-Workflow/1.0",
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                self.GEOCODING_URL,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        
        results = data.get("results", [])
        if not results:
            return None
        
        result = results[0]
        return {
            "name": result.get("name", location),
            "country": result.get("country", ""),
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
        }
    
    async def _fetch_weather(
        self,
        latitude: float,
        longitude: float,
        units: str,
        include_forecast: bool,
        forecast_days: int,
        timeout: float,
    ) -> Dict[str, Any]:
        """
        Fetch weather data from Open-Meteo API.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            units: Temperature units
            include_forecast: Include forecast data
            forecast_days: Number of forecast days
            timeout: Request timeout
            
        Returns:
            Dictionary with weather data
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                       "precipitation,weather_code,cloud_cover,pressure_msl,"
                       "wind_speed_10m,wind_direction_10m",
            "timezone": "auto",
        }
        
        if units == "fahrenheit":
            params["temperature_unit"] = "fahrenheit"
            params["wind_speed_unit"] = "mph"
        else:
            params["temperature_unit"] = "celsius"
            params["wind_speed_unit"] = "kmh"
        
        if include_forecast:
            params["forecast_days"] = min(forecast_days, 16)
            params["daily"] = ("weather_code,temperature_2m_max,temperature_2m_min,"
                              "precipitation_sum,wind_speed_10m_max")
        
        headers = {
            "User-Agent": "OpenCode-Workflow/1.0",
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                self.WEATHER_URL,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        
        result: Dict[str, Any] = {
            "current": self._parse_current_weather(data.get("current", {}), units),
        }
        
        if include_forecast and "daily" in data:
            result["forecast"] = self._parse_forecast(data.get("daily", {}), units)
        
        return result
    
    def _parse_current_weather(
        self,
        data: Dict[str, Any],
        units: str,
    ) -> Dict[str, Any]:
        """Parse current weather data."""
        temp_unit = "°F" if units == "fahrenheit" else "°C"
        speed_unit = "mph" if units == "fahrenheit" else "km/h"
        
        return {
            "temperature": f"{data.get('temperature_2m', 'N/A')}{temp_unit}",
            "feels_like": f"{data.get('apparent_temperature', 'N/A')}{temp_unit}",
            "humidity": f"{data.get('relative_humidity_2m', 'N/A')}%",
            "precipitation": f"{data.get('precipitation', 0)} mm",
            "weather_code": data.get("weather_code", 0),
            "weather_description": self._weather_code_to_description(
                data.get("weather_code", 0)
            ),
            "cloud_cover": f"{data.get('cloud_cover', 'N/A')}%",
            "pressure": f"{data.get('pressure_msl', 'N/A')} hPa",
            "wind_speed": f"{data.get('wind_speed_10m', 'N/A')} {speed_unit}",
            "wind_direction": self._degrees_to_direction(
                data.get("wind_direction_10m", 0)
            ),
        }
    
    def _parse_forecast(
        self,
        data: Dict[str, Any],
        units: str,
    ) -> List[Dict[str, Any]]:
        """Parse forecast data."""
        temp_unit = "°F" if units == "fahrenheit" else "°C"
        speed_unit = "mph" if units == "fahrenheit" else "km/h"
        
        forecast = []
        times = data.get("time", [])
        
        for i, date in enumerate(times):
            forecast.append({
                "date": date,
                "weather_code": data.get("weather_code", [])[i] if i < len(data.get("weather_code", [])) else 0,
                "weather_description": self._weather_code_to_description(
                    data.get("weather_code", [])[i] if i < len(data.get("weather_code", [])) else 0
                ),
                "temp_max": f"{data.get('temperature_2m_max', [])[i] if i < len(data.get('temperature_2m_max', [])) else 'N/A'}{temp_unit}",
                "temp_min": f"{data.get('temperature_2m_min', [])[i] if i < len(data.get('temperature_2m_min', [])) else 'N/A'}{temp_unit}",
                "precipitation": f"{data.get('precipitation_sum', [])[i] if i < len(data.get('precipitation_sum', [])) else 0} mm",
                "wind_speed_max": f"{data.get('wind_speed_10m_max', [])[i] if i < len(data.get('wind_speed_10m_max', [])) else 'N/A'} {speed_unit}",
            })
        
        return forecast
    
    def _weather_code_to_description(self, code: int) -> str:
        """Convert WMO weather code to description."""
        codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        return codes.get(code, "Unknown")
    
    def _degrees_to_direction(self, degrees: int) -> str:
        """Convert wind degrees to direction."""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]
