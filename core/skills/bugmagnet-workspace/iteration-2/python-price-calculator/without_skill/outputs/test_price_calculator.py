"""Existing tests for price_calculator."""
import pytest
from price_calculator import calculate_discount, calculate_total, format_price


def test_calculate_discount_basic():
    assert calculate_discount(100, 10) == 90.0


def test_calculate_total_single_item():
    items = [{"name": "Widget", "price": 10.0, "quantity": 1}]
    result = calculate_total(items)
    assert result["subtotal"] == 10.0
    assert result["total"] == 12.1


def test_format_price_eur():
    assert format_price(10.5) == "€10.50"
