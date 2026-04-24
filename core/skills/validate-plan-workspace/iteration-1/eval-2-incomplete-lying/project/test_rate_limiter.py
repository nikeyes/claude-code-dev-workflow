import pytest
from rate_limiter import RateLimiter


def test_allows_initial_login():
    rl = RateLimiter()
    assert not rl.is_blocked("alice")


def test_blocks_after_max_failures():
    rl = RateLimiter(max_attempts=3)
    for _ in range(3):
        rl.record_attempt("bob", success=False)
    assert rl.is_blocked("bob")


def test_resets_on_success():
    rl = RateLimiter(max_attempts=3)
    rl.record_attempt("carol", success=False)
    rl.record_attempt("carol", success=False)
    rl.record_attempt("carol", success=True)
    assert not rl.is_blocked("carol")


def test_does_not_affect_other_users():
    rl = RateLimiter(max_attempts=2)
    rl.record_attempt("dave", success=False)
    rl.record_attempt("dave", success=False)
    assert rl.is_blocked("dave")
    assert not rl.is_blocked("eve")
