import pytest
from calculator import add, subtract, multiply, divide, power, modulo


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 0) == 0


def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-2, 5) == -10


def test_divide():
    assert divide(10, 2) == 5.0
    assert divide(7, 2) == 3.5


def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)


def test_power():
    assert power(2, 3) == 8
    assert power(2, -1) == 0.5
    assert power(5, 0) == 1


def test_modulo():
    assert modulo(10, 3) == 1
    assert modulo(7, 2) == 1


def test_modulo_by_zero():
    with pytest.raises(ValueError, match="Cannot modulo by zero"):
        modulo(10, 0)
