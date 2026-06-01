"""BugMagnet edge-case tests for validator.py."""

import pytest
from validator import validate_email, validate_username


# ---------------------------------------------------------------------------
# validate_email — edge cases
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="validate_email accepts bare '@' as valid - BUG")
def test_email_bare_at_sign():
    """
    ROOT CAUSE: validate_email only checks `"@" in email`; a bare '@' passes
                but has no local part or domain.
    CODE LOCATION: validator.py:2
    PROPOSED FIX: Require non-empty local and domain parts, e.g.
                  `parts = email.split("@"); return len(parts)==2 and all(parts)`
    EXPECTED: False
    ACTUAL: True
    """
    assert validate_email("@") is False


def test_email_double_at_sign():
    """'@@' contains '@' so returns True — may or may not be desired."""
    # Documenting current behaviour: True
    assert validate_email("@@") is True


@pytest.mark.skip(reason="validate_email accepts missing local part - BUG")
def test_email_missing_local_part():
    """
    ROOT CAUSE: Only `"@" in email` is checked; '@example.com' passes.
    CODE LOCATION: validator.py:2
    PROPOSED FIX: Same as test_email_bare_at_sign — require non-empty parts.
    EXPECTED: False
    ACTUAL: True
    """
    assert validate_email("@example.com") is False


@pytest.mark.skip(reason="validate_email accepts missing domain - BUG")
def test_email_missing_domain():
    """
    ROOT CAUSE: Only `"@" in email` is checked; 'user@' passes.
    CODE LOCATION: validator.py:2
    PROPOSED FIX: Same as test_email_bare_at_sign — require non-empty parts.
    EXPECTED: False
    ACTUAL: True
    """
    assert validate_email("user@") is False


def test_email_spaces_around_at():
    """' @ ' contains '@' so currently returns True."""
    # Documenting current behaviour
    assert validate_email(" @ ") is True


def test_email_empty_string():
    assert validate_email("") is False


@pytest.mark.skip(reason="validate_email crashes on None - BUG")
def test_email_none_input():
    """
    ROOT CAUSE: `"@" in email` uses Python's `in` operator which requires
                an iterable; None is not iterable.
    CODE LOCATION: validator.py:2
    PROPOSED FIX: Add `if not isinstance(email, str): return False` guard.
    EXPECTED: returns False
    ACTUAL: TypeError: argument of type 'NoneType' is not iterable
    """
    assert validate_email(None) is False


@pytest.mark.skip(reason="validate_email crashes on non-string input - BUG")
def test_email_integer_input():
    """
    ROOT CAUSE: Same as None — `in` operator on an int raises TypeError.
    CODE LOCATION: validator.py:2
    PROPOSED FIX: Add `if not isinstance(email, str): return False` guard.
    EXPECTED: returns False
    ACTUAL: TypeError: argument of type 'int' is not iterable
    """
    assert validate_email(123) is False


# ---------------------------------------------------------------------------
# validate_username — boundary conditions
# ---------------------------------------------------------------------------

def test_username_exactly_3_chars():
    assert validate_username("abc") is True


def test_username_exactly_20_chars():
    assert validate_username("a" * 20) is True


def test_username_2_chars_is_too_short():
    assert validate_username("ab") is False


def test_username_21_chars_is_too_long():
    assert validate_username("a" * 21) is False


# ---------------------------------------------------------------------------
# validate_username — allowed character boundaries
# ---------------------------------------------------------------------------

def test_username_underscore_only():
    """Three underscores: meets length and char rules."""
    assert validate_username("___") is True


def test_username_starts_with_underscore():
    assert validate_username("_alice") is True


def test_username_ends_with_underscore():
    assert validate_username("alice_") is True


def test_username_digits_only():
    """All digits are alphanumeric, so '123' is valid per current rules."""
    assert validate_username("123") is True


def test_username_mixed_case():
    assert validate_username("Alice_123") is True


def test_username_hyphen_rejected():
    assert validate_username("al-ice") is False


def test_username_dot_rejected():
    assert validate_username("al.ice") is False


def test_username_space_rejected():
    assert validate_username("al ice") is False


def test_username_newline_rejected():
    assert validate_username("alice\n") is False


def test_username_tab_rejected():
    assert validate_username("alice\t") is False


def test_username_null_byte_rejected():
    assert validate_username("alice\x00") is False


# ---------------------------------------------------------------------------
# validate_username — unicode / non-ASCII
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="validate_username accepts unicode letters - BUG")
def test_username_unicode_letter_rejected():
    """
    ROOT CAUSE: Python's str.isalnum() returns True for accented letters
                (e.g. 'é', 'Ω') and non-ASCII digits ('١'), so the guard
                `c.isalnum() or c == '_'` permits any Unicode alphanumeric.
    CODE LOCATION: validator.py:10
    PROPOSED FIX: Use regex `re.fullmatch(r'[a-zA-Z0-9_]{3,20}', username)`
                  to restrict to ASCII alphanumeric + underscore.
    EXPECTED: validate_username('alicé') returns False
    ACTUAL: returns True
    """
    assert validate_username("alicé") is False


@pytest.mark.skip(reason="validate_username accepts non-ASCII digits - BUG")
def test_username_arabic_indic_digit_rejected():
    """
    ROOT CAUSE: Arabic-Indic digit '١' passes isalnum() check.
    CODE LOCATION: validator.py:10
    PROPOSED FIX: Use `re.fullmatch(r'[a-zA-Z0-9_]{3,20}', username)`.
    EXPECTED: False
    ACTUAL: True
    """
    assert validate_username("ali١") is False


# ---------------------------------------------------------------------------
# validate_username — non-string inputs
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="validate_username crashes on integer input - BUG")
def test_username_integer_input():
    """
    ROOT CAUSE: `len(username)` raises TypeError for non-string inputs.
    CODE LOCATION: validator.py:7
    PROPOSED FIX: Add `if not isinstance(username, str): return False` guard.
    EXPECTED: returns False
    ACTUAL: TypeError: object of type 'int' has no len()
    """
    assert validate_username(123) is False
