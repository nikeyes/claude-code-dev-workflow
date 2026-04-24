import pytest
from calculator import add, subtract


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 0) == 0


def test_multiply():
    from calculator import multiply
    assert multiply(3, 4) == 12
    assert multiply(-2, 5) == -10
    assert multiply(0, 100) == 0


def test_divide():
    from calculator import divide
    assert divide(10, 2) == 5.0
    assert divide(7, 2) == 3.5


def test_divide_by_zero():
    from calculator import divide
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)
