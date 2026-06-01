import pytest
from converter import celsius_to_fahrenheit, fahrenheit_to_celsius


def test_c_to_f_boiling():
    assert celsius_to_fahrenheit(100) == 212


def test_c_to_f_freezing():
    assert celsius_to_fahrenheit(0) == 32


def test_f_to_c_boiling():
    assert fahrenheit_to_celsius(212) == 100


def test_f_to_c_freezing():
    assert fahrenheit_to_celsius(32) == 0


# --- Phase 1: kg/lb ---

def test_kg_to_lb():
    from converter import kg_to_lb
    assert round(kg_to_lb(1), 2) == 2.20


def test_lb_to_kg():
    from converter import lb_to_kg
    assert round(lb_to_kg(2.20462), 2) == 1.00


# --- Phase 2: km/miles ---

def test_km_to_miles():
    from converter import km_to_miles
    assert round(km_to_miles(1), 4) == 0.6214


def test_miles_to_km():
    from converter import miles_to_km
    assert round(miles_to_km(1), 4) == 1.6093
