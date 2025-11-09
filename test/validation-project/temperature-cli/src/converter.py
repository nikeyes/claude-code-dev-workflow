"""Temperature conversion functions.

This module provides conversions between temperature scales.
Currently supports Celsius and Fahrenheit only.
"""

import argparse
import sys


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit.

    Args:
        celsius: Temperature in Celsius

    Returns:
        Temperature in Fahrenheit
    """
    return (celsius * 9/5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius.

    Args:
        fahrenheit: Temperature in Fahrenheit

    Returns:
        Temperature in Celsius
    """
    return (fahrenheit - 32) * 5/9


# NOTE: Kelvin conversions intentionally missing for workflow testing
# TODO(3): Add celsius_to_kelvin() function
# TODO(3): Add kelvin_to_celsius() function
# TODO(3): Add kelvin CLI support


def main():
    """CLI entry point for temperature conversions."""
    parser = argparse.ArgumentParser(description="Convert temperatures between scales")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--celsius", type=float, help="Convert from Celsius to Fahrenheit")
    group.add_argument("--fahrenheit", type=float, help="Convert from Fahrenheit to Celsius")
    # NOTE: --kelvin argument intentionally missing

    args = parser.parse_args()

    if args.celsius is not None:
        result = celsius_to_fahrenheit(args.celsius)
        print(f"{args.celsius}°C = {result:.2f}°F")
    elif args.fahrenheit is not None:
        result = fahrenheit_to_celsius(args.fahrenheit)
        print(f"{args.fahrenheit}°F = {result:.2f}°C")


if __name__ == "__main__":
    main()
