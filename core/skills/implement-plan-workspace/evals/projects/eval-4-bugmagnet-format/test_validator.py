import pytest
from validator import validate_email


def test_valid_email():
    assert validate_email("user@example.com") is True


def test_missing_at_sign():
    assert validate_email("userexample.com") is False


# --- Phase 1 tests: validate_username ---

def test_valid_username():
    from validator import validate_username
    assert validate_username("alice123") is True


def test_username_too_short():
    from validator import validate_username
    assert validate_username("ab") is False


def test_username_too_long():
    from validator import validate_username
    assert validate_username("a" * 21) is False


def test_username_invalid_chars():
    from validator import validate_username
    assert validate_username("alice!") is False


def test_username_empty():
    from validator import validate_username
    assert validate_username("") is False
