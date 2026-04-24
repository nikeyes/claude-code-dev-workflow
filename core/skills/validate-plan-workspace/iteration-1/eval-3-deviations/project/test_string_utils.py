import pytest
from string_utils import shorten, slugify, count_words, extract_emails, mask_sensitive, reverse_words


def test_shorten():
    assert shorten("Hello World", 8) == "Hello..."
    assert shorten("Hi", 10) == "Hi"


def test_shorten_invalid():
    with pytest.raises(ValueError):
        shorten("test", 2)


def test_slugify():
    assert slugify("Hello World!") == "hello-world"
    assert slugify("  Spaces  Everywhere  ") == "spaces-everywhere"


def test_count_words():
    assert count_words("one two three") == 3
    assert count_words("") == 0


def test_extract_emails():
    assert extract_emails("contact foo@bar.com") == ["foo@bar.com"]
    assert extract_emails("no emails here") == []


def test_mask_sensitive():
    assert mask_sensitive("card 1234-5678", "1234-5678") == "card ***"


def test_reverse_words():
    assert reverse_words("hello world") == "world hello"
