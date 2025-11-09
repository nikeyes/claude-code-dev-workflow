"""Tests for temperature conversion functions."""

from src.converter import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
)


class TestCelsiusToFahrenheit:
    """Test Celsius to Fahrenheit conversions."""

    def test_freezing_point(self):
        """Water freezes at 0°C = 32°F."""
        assert celsius_to_fahrenheit(0) == 32

    def test_boiling_point(self):
        """Water boils at 100°C = 212°F."""
        assert celsius_to_fahrenheit(100) == 212

    def test_room_temperature(self):
        """Room temperature ~25°C = 77°F."""
        assert celsius_to_fahrenheit(25) == 77

    def test_negative_temperature(self):
        """Test negative Celsius values."""
        assert celsius_to_fahrenheit(-40) == -40


class TestFahrenheitToCelsius:
    """Test Fahrenheit to Celsius conversions."""

    def test_freezing_point(self):
        """Water freezes at 32°F = 0°C."""
        assert fahrenheit_to_celsius(32) == 0

    def test_boiling_point(self):
        """Water boils at 212°F = 100°C."""
        assert fahrenheit_to_celsius(212) == 100

    def test_room_temperature(self):
        """Room temperature ~77°F = 25°C."""
        assert fahrenheit_to_celsius(77) == 25

    def test_negative_temperature(self):
        """Test negative Fahrenheit values."""
        assert fahrenheit_to_celsius(-40) == -40


# NOTE: Kelvin tests intentionally missing
# TODO(3): Add TestCelsiusToKelvin class
# TODO(3): Add TestKelvinToCelsius class
