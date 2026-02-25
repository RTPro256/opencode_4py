"""
Tests for WeatherTool.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from opencode.workflow.tools.weather import WeatherTool
from opencode.workflow.tools.registry import ToolResult


class TestWeatherTool:
    """Tests for WeatherTool class."""

    def test_get_schema(self):
        """Test getting tool schema."""
        schema = WeatherTool.get_schema()
        assert schema.name == "weather"
        assert "location" in schema.parameters["properties"]
        assert schema.requires_auth is False

    @pytest.mark.asyncio
    async def test_execute_missing_location(self):
        """Test execute with missing location parameter."""
        tool = WeatherTool(config={})
        result = await tool.execute({})
        assert result.success is False
        assert result.error is not None
        assert "location" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_with_coordinates(self):
        """Test execute with coordinates instead of location name."""
        tool = WeatherTool(config={})
        
        geocode_response = MagicMock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = {
            "results": [{"name": "Toronto", "country": "Canada", "latitude": 43.65, "longitude": -79.38}]
        }
        
        weather_response = MagicMock()
        weather_response.status_code = 200
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 20,
                "apparent_temperature": 22,
                "relative_humidity_2m": 65,
                "precipitation": 0,
                "weather_code": 0,
                "cloud_cover": 10,
                "pressure_msl": 1013,
                "wind_speed_10m": 15,
                "wind_direction_10m": 180,
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            call_count = [0]
            
            async def side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    return geocode_response
                return weather_response
            
            mock_instance.get = side_effect
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"location": "43.65, -79.38"})

        assert result.success is True
        assert result.data["location"]["latitude"] == 43.65

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful weather fetch."""
        tool = WeatherTool(config={})
        
        geocode_response = MagicMock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = {
            "results": [{"name": "Toronto", "country": "Canada", "latitude": 43.65, "longitude": -79.38}]
        }
        
        weather_response = MagicMock()
        weather_response.status_code = 200
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 20,
                "apparent_temperature": 22,
                "relative_humidity_2m": 65,
                "precipitation": 0,
                "weather_code": 0,
                "cloud_cover": 10,
                "pressure_msl": 1013,
                "wind_speed_10m": 15,
                "wind_direction_10m": 180,
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            call_count = [0]
            
            async def side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    return geocode_response
                return weather_response
            
            mock_instance.get = side_effect
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"location": "Toronto, Canada"})

        assert result.success is True
        assert result.data["location"]["name"] == "Toronto"
        assert "current" in result.data

    @pytest.mark.asyncio
    async def test_execute_with_forecast(self):
        """Test weather fetch with forecast."""
        tool = WeatherTool(config={})
        
        geocode_response = MagicMock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = {
            "results": [{"name": "Toronto", "country": "Canada", "latitude": 43.65, "longitude": -79.38}]
        }
        
        weather_response = MagicMock()
        weather_response.status_code = 200
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 20,
                "apparent_temperature": 22,
                "relative_humidity_2m": 65,
                "precipitation": 0,
                "weather_code": 0,
                "cloud_cover": 10,
                "pressure_msl": 1013,
                "wind_speed_10m": 15,
                "wind_direction_10m": 180,
            },
            "daily": {
                "time": ["2024-01-01", "2024-01-02"],
                "weather_code": [0, 1],
                "temperature_2m_max": [25, 26],
                "temperature_2m_min": [15, 16],
                "precipitation_sum": [0, 0],
                "wind_speed_10m_max": [20, 22],
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            call_count = [0]
            
            async def side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    return geocode_response
                return weather_response
            
            mock_instance.get = side_effect
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({
                "location": "Toronto",
                "include_forecast": True,
                "forecast_days": 7,
            })

        assert result.success is True
        assert "forecast" in result.data
        assert result.data["forecast"] is not None

    @pytest.mark.asyncio
    async def test_execute_fahrenheit(self):
        """Test weather fetch with fahrenheit units."""
        tool = WeatherTool(config={})
        
        geocode_response = MagicMock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = {
            "results": [{"name": "New York", "country": "USA", "latitude": 40.71, "longitude": -74.01}]
        }
        
        weather_response = MagicMock()
        weather_response.status_code = 200
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 68,
                "apparent_temperature": 70,
                "relative_humidity_2m": 60,
                "precipitation": 0,
                "weather_code": 0,
                "cloud_cover": 5,
                "pressure_msl": 1015,
                "wind_speed_10m": 10,
                "wind_direction_10m": 90,
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            call_count = [0]
            
            async def side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    return geocode_response
                return weather_response
            
            mock_instance.get = side_effect
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"location": "New York", "units": "fahrenheit"})

        assert result.success is True
        assert result.data["units"] == "fahrenheit"

    @pytest.mark.asyncio
    async def test_execute_location_not_found(self):
        """Test execute when location is not found."""
        tool = WeatherTool(config={})
        
        geocode_response = MagicMock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = {"results": []}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=geocode_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"location": "NonexistentPlace12345"})

        assert result.success is False
        assert result.error is not None
        assert "not find" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test execute when request times out."""
        tool = WeatherTool(config={})

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"location": "Toronto"})

        assert result.success is False
        assert result.error is not None
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_exception(self):
        """Test execute when unexpected exception occurs."""
        tool = WeatherTool(config={})

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("Unexpected error"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool.execute({"location": "Toronto"})

        assert result.success is False
        assert result.error is not None
        assert "failed" in result.error.lower()

    def test_weather_code_to_description(self):
        """Test weather code to description conversion."""
        tool = WeatherTool(config={})
        
        assert tool._weather_code_to_description(0) == "Clear sky"
        assert tool._weather_code_to_description(1) == "Mainly clear"
        assert tool._weather_code_to_description(61) == "Slight rain"
        assert tool._weather_code_to_description(95) == "Thunderstorm"
        assert tool._weather_code_to_description(999) == "Unknown"

    def test_degrees_to_direction(self):
        """Test wind degrees to direction conversion."""
        tool = WeatherTool(config={})
        
        assert tool._degrees_to_direction(0) == "N"
        assert tool._degrees_to_direction(90) == "E"
        assert tool._degrees_to_direction(180) == "S"
        assert tool._degrees_to_direction(270) == "W"

    def test_parse_current_weather(self):
        """Test parsing current weather data."""
        tool = WeatherTool(config={})
        
        data = {
            "temperature_2m": 20,
            "apparent_temperature": 22,
            "relative_humidity_2m": 65,
            "precipitation": 0,
            "weather_code": 0,
            "cloud_cover": 10,
            "pressure_msl": 1013,
            "wind_speed_10m": 15,
            "wind_direction_10m": 180,
        }
        
        result = tool._parse_current_weather(data, "celsius")
        
        assert "20°C" in result["temperature"]
        assert "65%" in result["humidity"]
        assert "Clear sky" == result["weather_description"]

    def test_parse_current_weather_fahrenheit(self):
        """Test parsing current weather data in fahrenheit."""
        tool = WeatherTool(config={})
        
        data = {
            "temperature_2m": 68,
            "apparent_temperature": 70,
            "relative_humidity_2m": 60,
            "precipitation": 0,
            "weather_code": 0,
            "cloud_cover": 5,
            "pressure_msl": 1015,
            "wind_speed_10m": 10,
            "wind_direction_10m": 90,
        }
        
        result = tool._parse_current_weather(data, "fahrenheit")
        
        assert "68°F" in result["temperature"]
        assert "mph" in result["wind_speed"]

    def test_parse_forecast(self):
        """Test parsing forecast data."""
        tool = WeatherTool(config={})
        
        data = {
            "time": ["2024-01-01", "2024-01-02"],
            "weather_code": [0, 1],
            "temperature_2m_max": [25, 26],
            "temperature_2m_min": [15, 16],
            "precipitation_sum": [0, 0],
            "wind_speed_10m_max": [20, 22],
        }
        
        result = tool._parse_forecast(data, "celsius")
        
        assert len(result) == 2
        assert result[0]["date"] == "2024-01-01"
        assert result[0]["weather_description"] == "Clear sky"

    @pytest.mark.asyncio
    async def test_geocode_with_name(self):
        """Test geocoding with location name."""
        tool = WeatherTool(config={})
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"name": "Toronto", "country": "Canada", "latitude": 43.65, "longitude": -79.38}]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool._geocode("Toronto", 30)

        assert result is not None
        assert result["name"] == "Toronto"
        assert result["latitude"] == 43.65

    @pytest.mark.asyncio
    async def test_geocode_with_coordinates(self):
        """Test geocoding with coordinates."""
        tool = WeatherTool(config={})
        
        result = await tool._geocode("43.65, -79.38", 30)
        
        assert result is not None
        assert result["latitude"] == 43.65
        assert result["longitude"] == -79.38

    @pytest.mark.asyncio
    async def test_geocode_invalid_coordinates(self):
        """Test geocoding with invalid coordinates string."""
        tool = WeatherTool(config={})
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            # Invalid coordinates string (not numbers)
            result = await tool._geocode("abc, def", 30)

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_weather(self):
        """Test fetching weather data."""
        tool = WeatherTool(config={})
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current": {
                "temperature_2m": 20,
                "apparent_temperature": 22,
                "relative_humidity_2m": 65,
                "precipitation": 0,
                "weather_code": 0,
                "cloud_cover": 10,
                "pressure_msl": 1013,
                "wind_speed_10m": 15,
                "wind_direction_10m": 180,
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await tool._fetch_weather(43.65, -79.38, "celsius", False, 7, 30)

        assert "current" in result
