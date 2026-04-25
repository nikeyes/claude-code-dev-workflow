import pytest
from sanitizer import DataSanitizer


def test_sanitize_string_strips_whitespace():
    s = DataSanitizer()
    assert s.sanitize_string("  hello  ") == "hello"


def test_sanitize_string_non_string():
    s = DataSanitizer()
    assert s.sanitize_string(42) == "42"


def test_sanitize_email_normalizes():
    s = DataSanitizer()
    assert s.sanitize_email("  User@Example.COM  ") == "user@example.com"


def test_sanitize_email_rejects_invalid():
    s = DataSanitizer()
    with pytest.raises(ValueError):
        s.sanitize_email("not-an-email")


def test_sanitize_html_escapes_tags():
    s = DataSanitizer()
    assert s.sanitize_html("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"


def test_sanitize_record_mixed_fields():
    s = DataSanitizer()
    record = {
        "name": "  Alice  ",
        "email": "Alice@Example.COM",
        "age": 30,
        "html_bio": "<b>Bold</b>",
    }
    result = s.sanitize_record(record)
    assert result["name"] == "Alice"
    assert result["email"] == "alice@example.com"
    assert result["age"] == 30
    assert "<b>" not in result["html_bio"]


def test_sanitize_record_empty():
    s = DataSanitizer()
    assert s.sanitize_record({}) == {}
