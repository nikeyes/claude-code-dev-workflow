"""Baseline tests for the rate limiter — happy path only."""

from rate_limiter import RateLimiter, create_rate_limiter


def test_allows_request_under_limit():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    assert rl.is_allowed("user1", now=100.0) is True


def test_blocks_after_tokens_exhausted():
    rl = RateLimiter(max_tokens=2, refill_rate=0.5)
    assert rl.is_allowed("user1", now=100.0) is True
    assert rl.is_allowed("user1", now=100.0) is True
    assert rl.is_allowed("user1", now=100.0) is False


def test_get_remaining_shows_token_count():
    rl = RateLimiter(max_tokens=10, refill_rate=1.0)
    rl.is_allowed("user1", now=100.0)
    status = rl.get_remaining("user1", now=100.0)
    assert status["remaining_tokens"] == 9.0
