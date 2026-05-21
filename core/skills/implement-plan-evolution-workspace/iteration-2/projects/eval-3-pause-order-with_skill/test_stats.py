import pytest
from stats import mean


def test_mean_single_value():
    assert mean([5]) == 5.0


def test_mean_multiple_values():
    assert mean([1, 2, 3]) == 2.0


def test_mean_empty_raises():
    with pytest.raises(ValueError, match="Cannot compute mean of empty list"):
        mean([])


# --- Phase 1 tests: median ---

def test_median_odd():
    from stats import median
    assert median([3, 1, 2]) == 2


def test_median_even():
    from stats import median
    assert median([4, 1, 3, 2]) == 2.5


def test_median_single():
    from stats import median
    assert median([7]) == 7


def test_median_empty_raises():
    from stats import median
    with pytest.raises(ValueError, match="Cannot compute median of empty list"):
        median([])


# --- Phase 2 tests: mode ---

def test_mode_single_mode():
    from stats import mode
    assert mode([1, 2, 2, 3]) == 2


def test_mode_multiple_values():
    from stats import mode
    result = mode([1, 1, 2, 2, 3])
    assert result in [1, 2]


def test_mode_empty_raises():
    from stats import mode
    with pytest.raises(ValueError, match="Cannot compute mode of empty list"):
        mode([])


# --- BugMagnet edge-case tests: mean ---

def test_mean_negative_values():
    assert mean([-1, -2, -3]) == -2.0


def test_mean_floats():
    assert mean([0.1, 0.2, 0.3]) == pytest.approx(0.2)


def test_mean_single_negative():
    assert mean([-5]) == -5.0


def test_mean_large_values():
    large = [10**15, 10**15, 10**15]
    assert mean(large) == 10**15


def test_mean_mixed_sign():
    assert mean([-1, 0, 1]) == 0.0


# --- BugMagnet edge-case tests: median ---

def test_median_negative_values():
    from stats import median
    assert median([-3, -1, -2]) == -2


def test_median_duplicates():
    from stats import median
    assert median([2, 2, 2]) == 2


def test_median_does_not_mutate_input():
    from stats import median
    original = [3, 1, 2]
    copy = original[:]
    median(original)
    assert original == copy


def test_median_two_elements():
    from stats import median
    assert median([1, 3]) == 2.0


def test_median_floats():
    from stats import median
    assert median([1.5, 2.5, 3.5]) == pytest.approx(2.5)


def test_median_already_sorted():
    from stats import median
    assert median([1, 2, 3, 4, 5]) == 3


def test_median_reverse_sorted():
    from stats import median
    assert median([5, 4, 3, 2, 1]) == 3


# --- BugMagnet edge-case tests: mode ---

def test_mode_single_element():
    from stats import mode
    assert mode([42]) == 42


def test_mode_all_same():
    from stats import mode
    assert mode([7, 7, 7]) == 7


def test_mode_negative_values():
    from stats import mode
    assert mode([-1, -1, -2]) == -1


def test_mode_float_values():
    from stats import mode
    assert mode([1.5, 1.5, 2.5]) == 1.5


def test_mode_string_values():
    from stats import mode
    assert mode(["a", "b", "a"]) == "a"


def test_mode_tie_returns_a_valid_value():
    from stats import mode
    # All elements appear once — any is valid
    result = mode([10, 20, 30])
    assert result in [10, 20, 30]
