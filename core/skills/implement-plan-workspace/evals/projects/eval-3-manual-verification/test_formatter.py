import pytest
from formatter import wrap_text


def test_wrap_short_text():
    assert wrap_text("hello world", width=80) == "hello world"


def test_wrap_at_boundary():
    result = wrap_text("one two three four five", width=10)
    lines = result.split("\n")
    assert all(len(line) <= 10 for line in lines)


def test_wrap_zero_width_raises():
    with pytest.raises(ValueError, match="Width must be positive"):
        wrap_text("hello", width=0)


def test_wrap_empty_string():
    assert wrap_text("", width=80) == ""


# --- Phase 1 tests: center_text ---

def test_center_text():
    from formatter import center_text
    result = center_text("hello", width=20)
    assert result == "       hello        "
    assert len(result) == 20


def test_center_text_longer_than_width():
    from formatter import center_text
    result = center_text("hello world", width=5)
    assert result == "hello world"


# --- Phase 2 tests: format_table ---

def test_format_table_basic():
    from formatter import format_table
    headers = ["Name", "Age"]
    rows = [["Alice", "30"], ["Bob", "25"]]
    result = format_table(headers, rows)
    assert "Name" in result
    assert "Alice" in result
    assert "---" in result


def test_format_table_alignment():
    from formatter import format_table
    headers = ["Name", "Score"]
    rows = [["A", "100"], ["Bob", "5"]]
    result = format_table(headers, rows)
    lines = result.strip().split("\n")
    assert len(set(len(line) for line in lines)) == 1


def test_format_table_empty_rows():
    from formatter import format_table
    result = format_table(["Col1", "Col2"], [])
    assert "Col1" in result
    lines = result.strip().split("\n")
    assert len(lines) == 2
