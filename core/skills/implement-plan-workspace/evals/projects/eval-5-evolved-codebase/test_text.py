import pytest


# --- Existing tests ---

def test_slugify():
    from text_utils import slugify
    assert slugify("Hello World") == "hello-world"
    assert slugify("  Spaces  ") == "spaces"


def test_word_count():
    from text_utils import word_count
    assert word_count("one two three") == 3
    assert word_count("") == 0


def test_truncate():
    from text_transforms import truncate
    assert truncate("Hello World", 8) == "Hello..."
    assert truncate("Hi", 10) == "Hi"


def test_title_case():
    from text_transforms import title_case
    assert title_case("hello world") == "Hello World"


# --- Phase 2 tests: search functions ---

def test_contains_any():
    from text_utils import contains_any
    assert contains_any("hello world", ["world", "foo"]) is True
    assert contains_any("hello world", ["foo", "bar"]) is False
    assert contains_any("hello world", []) is False


def test_extract_emails():
    from text_utils import extract_emails
    text = "Contact alice@example.com or bob@test.org for info"
    emails = extract_emails(text)
    assert "alice@example.com" in emails
    assert "bob@test.org" in emails


# --- Phase 3 tests: pad functions ---

def test_pad_right():
    from text_transforms import pad_right
    assert pad_right("hi", 10) == "hi        "
    assert pad_right("hello", 3) == "hello"


def test_pad_center():
    from text_transforms import pad_center
    result = pad_center("hi", 10)
    assert len(result) == 10
    assert result.strip() == "hi"


def test_repeat_text():
    from text_transforms import repeat_text
    assert repeat_text("ab", 3) == "ababab"
    assert repeat_text("x", 0) == ""
