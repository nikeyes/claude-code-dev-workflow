"""Comprehensive tests for the rate limiter — edge cases, boundary conditions, and bugs."""

import pytest
from rate_limiter import RateLimiter, create_rate_limiter, create_burst_limiter


# ---------------------------------------------------------------------------
# Existing baseline tests (preserved)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Token bucket: basic refill behaviour
# ---------------------------------------------------------------------------

def test_tokens_refill_over_time():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    # Drain all 5 tokens
    for _ in range(5):
        assert rl.is_allowed("user1", now=100.0) is True
    assert rl.is_allowed("user1", now=100.0) is False

    # After 3 seconds at rate 1.0, 3 tokens should be available
    assert rl.is_allowed("user1", now=103.0) is True
    assert rl.is_allowed("user1", now=103.0) is True
    assert rl.is_allowed("user1", now=103.0) is True
    assert rl.is_allowed("user1", now=103.0) is False


def test_tokens_do_not_exceed_max_on_refill():
    rl = RateLimiter(max_tokens=5, refill_rate=10.0)
    rl.is_allowed("user1", now=100.0)  # consume 1 token (4 left)
    # Wait long enough that refill would exceed max if uncapped
    status = rl.get_remaining("user1", now=200.0)
    assert status["remaining_tokens"] == 5.0


def test_partial_refill_allows_partial_requests():
    rl = RateLimiter(max_tokens=2, refill_rate=1.0)
    rl.is_allowed("user1", now=100.0)
    rl.is_allowed("user1", now=100.0)
    # 0 tokens left; after 0.5 seconds only 0.5 tokens refilled — not enough
    assert rl.is_allowed("user1", now=100.5) is False
    # After 1 full second, 1 token refilled — enough for cost=1
    assert rl.is_allowed("user1", now=101.0) is True


def test_refill_with_same_timestamp_does_not_add_tokens():
    rl = RateLimiter(max_tokens=3, refill_rate=5.0)
    rl.is_allowed("user1", now=100.0)  # 2 tokens left
    # Calling again at the same timestamp should not refill
    status = rl.get_remaining("user1", now=100.0)
    assert status["remaining_tokens"] == 2.0


# ---------------------------------------------------------------------------
# Token bucket: cost parameter
# ---------------------------------------------------------------------------

def test_is_allowed_with_fractional_cost():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    assert rl.is_allowed("user1", cost=0.5, now=100.0) is True
    status = rl.get_remaining("user1", now=100.0)
    assert status["remaining_tokens"] == 4.5


def test_is_allowed_with_cost_equal_to_max_tokens():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    # A request costing exactly max_tokens should be allowed on a fresh key
    assert rl.is_allowed("user1", cost=5.0, now=100.0) is True
    assert rl.is_allowed("user1", cost=1.0, now=100.0) is False


def test_is_allowed_with_cost_exceeding_max_tokens_is_never_allowed():
    """A cost greater than max_tokens can never be satisfied."""
    rl = RateLimiter(max_tokens=3, refill_rate=1.0)
    # Even on a brand-new key the bucket only has max_tokens
    assert rl.is_allowed("user1", cost=4.0, now=100.0) is False
    # And waiting won't help since cap is 3
    assert rl.is_allowed("user1", cost=4.0, now=200.0) is False


def test_is_allowed_cost_zero_always_allowed():
    """
    BUG: cost=0 is always allowed and appends a timestamp each call,
    causing unbounded growth of request_timestamps without consuming tokens.
    This test documents the current (buggy) behaviour.
    """
    rl = RateLimiter(max_tokens=0, refill_rate=0.0)
    # Even with max_tokens=0, cost=0 should pass the `tokens >= cost` check
    assert rl.is_allowed("user1", cost=0.0, now=100.0) is True
    # Timestamps accumulate
    status = rl.get_remaining("user1", now=100.0)
    assert status["requests_in_window"] == 1


def test_is_allowed_negative_cost_inflates_tokens():
    """
    BUG: A negative cost causes tokens to be *increased* (tokens -= negative_cost)
    which can push tokens above max_tokens.
    This test documents the current (buggy) behaviour.
    """
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    rl.is_allowed("user1", cost=1.0, now=100.0)  # 4 tokens left
    rl.is_allowed("user1", cost=-3.0, now=100.0)  # tokens become 4 - (-3) = 7
    status = rl.get_remaining("user1", now=100.0)
    assert status["remaining_tokens"] > rl.max_tokens  # BUG: exceeds max


# ---------------------------------------------------------------------------
# Key isolation
# ---------------------------------------------------------------------------

def test_different_keys_are_independent():
    rl = RateLimiter(max_tokens=2, refill_rate=0.5)
    rl.is_allowed("a", now=100.0)
    rl.is_allowed("a", now=100.0)
    # "a" is exhausted; "b" should still be allowed
    assert rl.is_allowed("a", now=100.0) is False
    assert rl.is_allowed("b", now=100.0) is True


def test_new_key_starts_with_full_bucket():
    rl = RateLimiter(max_tokens=10, refill_rate=1.0)
    status = rl.get_remaining("brand_new", now=100.0)
    assert status["remaining_tokens"] == 10.0


# ---------------------------------------------------------------------------
# Sliding window: request_timestamps tracking
# ---------------------------------------------------------------------------

def test_requests_in_window_counts_recent_requests():
    rl = RateLimiter(max_tokens=10, refill_rate=5.0, window_seconds=60.0)
    for i in range(4):
        rl.is_allowed("user1", now=100.0 + i)
    status = rl.get_remaining("user1", now=103.0)
    assert status["requests_in_window"] == 4


def test_requests_outside_window_are_excluded():
    rl = RateLimiter(max_tokens=10, refill_rate=5.0, window_seconds=10.0)
    rl.is_allowed("user1", now=100.0)  # at t=100, window covers (90, 100]
    rl.is_allowed("user1", now=105.0)  # at t=105
    # At t=111, the request at t=100 is outside the 10-second window
    status = rl.get_remaining("user1", now=111.0)
    assert status["requests_in_window"] == 1  # only t=105 remains


def test_request_exactly_at_window_boundary_is_excluded():
    """
    The _clean_window uses ts > cutoff (strictly greater).
    A timestamp exactly equal to cutoff is dropped.
    This test documents that boundary behaviour.
    """
    rl = RateLimiter(max_tokens=10, refill_rate=5.0, window_seconds=10.0)
    rl.is_allowed("user1", now=100.0)
    # At t=110, cutoff = 110 - 10 = 100; ts=100 is NOT > 100, so it's dropped
    status = rl.get_remaining("user1", now=110.0)
    assert status["requests_in_window"] == 0


def test_denied_request_not_added_to_timestamps():
    rl = RateLimiter(max_tokens=1, refill_rate=0.5)
    rl.is_allowed("user1", now=100.0)  # allowed
    rl.is_allowed("user1", now=100.0)  # denied
    status = rl.get_remaining("user1", now=100.0)
    assert status["requests_in_window"] == 1


# ---------------------------------------------------------------------------
# get_wait_time
# ---------------------------------------------------------------------------

def test_get_wait_time_zero_when_tokens_available():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    assert rl.get_wait_time("user1", cost=1.0, now=100.0) == 0.0


def test_get_wait_time_positive_when_tokens_exhausted():
    rl = RateLimiter(max_tokens=2, refill_rate=1.0)
    rl.is_allowed("user1", now=100.0)
    rl.is_allowed("user1", now=100.0)
    # deficit = 1, refill_rate = 1.0 => wait = 1.0 second
    assert rl.get_wait_time("user1", cost=1.0, now=100.0) == pytest.approx(1.0)


def test_get_wait_time_scales_with_cost():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    for _ in range(5):
        rl.is_allowed("user1", now=100.0)
    # Need 3 tokens, refill_rate=1.0 => wait = 3.0
    assert rl.get_wait_time("user1", cost=3.0, now=100.0) == pytest.approx(3.0)


def test_get_wait_time_zero_after_sufficient_refill():
    rl = RateLimiter(max_tokens=2, refill_rate=1.0)
    rl.is_allowed("user1", now=100.0)
    rl.is_allowed("user1", now=100.0)
    # After 2 seconds the bucket is full again
    assert rl.get_wait_time("user1", cost=1.0, now=102.0) == 0.0


def test_get_wait_time_with_refill_rate_zero_raises():
    """
    BUG: When refill_rate=0 and tokens are insufficient,
    get_wait_time divides by zero, raising ZeroDivisionError.
    """
    rl = RateLimiter(max_tokens=1, refill_rate=0.0)
    rl.is_allowed("user1", now=100.0)  # drain the single token
    with pytest.raises(ZeroDivisionError):
        rl.get_wait_time("user1", cost=1.0, now=100.0)


def test_get_wait_time_for_new_key_does_not_raise():
    """get_wait_time on a brand-new key should return 0.0 (bucket full)."""
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    assert rl.get_wait_time("never_seen", cost=1.0, now=100.0) == 0.0


# ---------------------------------------------------------------------------
# get_remaining / resets_at semantics
# ---------------------------------------------------------------------------

def test_get_remaining_contains_expected_keys():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    status = rl.get_remaining("user1", now=100.0)
    assert set(status.keys()) == {"remaining_tokens", "requests_in_window", "window_seconds", "resets_at"}


def test_get_remaining_window_seconds_matches_config():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=30.0)
    status = rl.get_remaining("user1", now=100.0)
    assert status["window_seconds"] == 30.0


def test_get_remaining_resets_at_is_misleading():
    """
    BUG: resets_at is computed as entry.last_refill + window_seconds.
    Because last_refill is updated to `now` on every _refill call,
    resets_at always equals now + window_seconds — it does not represent
    a fixed, meaningful reset point.  Each successive call shifts it forward.
    """
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    status1 = rl.get_remaining("user1", now=100.0)
    status2 = rl.get_remaining("user1", now=110.0)
    # Both calls yield resets_at = now + 60 rather than a stable future timestamp
    assert status1["resets_at"] == pytest.approx(160.0)
    assert status2["resets_at"] == pytest.approx(170.0)  # shifted — BUG


# ---------------------------------------------------------------------------
# cleanup_expired
# ---------------------------------------------------------------------------

def test_cleanup_removes_idle_entries():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("user1", now=100.0)
    # threshold = 60 * 2 = 120 seconds; at t=221 the entry is idle for 121 s
    removed = rl.cleanup_expired(now=221.0)
    assert removed == 1
    assert "user1" not in rl.get_all_keys()


def test_cleanup_keeps_recently_active_entries():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("user1", now=100.0)
    # Only 100 seconds have passed — below the 120-second threshold
    removed = rl.cleanup_expired(now=200.0)
    assert removed == 0
    assert "user1" in rl.get_all_keys()


def test_cleanup_returns_count_of_removed_entries():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("a", now=100.0)
    rl.is_allowed("b", now=100.0)
    rl.is_allowed("c", now=100.0)
    removed = rl.cleanup_expired(now=400.0)
    assert removed == 3


def test_cleanup_does_not_remove_freshly_queried_entries():
    """
    BUG: Any method that calls _refill (get_remaining, get_wait_time)
    updates last_refill to `now`, which resets the expiry clock.
    An entry that is only queried — never actively used — will never expire
    as long as queries continue.  This test documents the behaviour.
    """
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("user1", now=100.0)
    # Simulate periodic status checks that keep bumping last_refill
    rl.get_remaining("user1", now=150.0)
    rl.get_remaining("user1", now=200.0)
    rl.get_remaining("user1", now=250.0)
    # last_refill is now 250; threshold requires now - 250 > 120
    removed = rl.cleanup_expired(now=350.0)
    # Entry was refreshed at 250 so only 100 s elapsed — NOT removed
    assert removed == 0  # the expiry clock was reset by get_remaining calls


def test_cleanup_on_empty_limiter_returns_zero():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    assert rl.cleanup_expired(now=9999.0) == 0


# ---------------------------------------------------------------------------
# get_all_keys
# ---------------------------------------------------------------------------

def test_get_all_keys_empty_initially():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    assert rl.get_all_keys() == []


def test_get_all_keys_returns_all_seen_keys():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    rl.is_allowed("a", now=100.0)
    rl.is_allowed("b", now=100.0)
    rl.get_remaining("c", now=100.0)
    assert sorted(rl.get_all_keys()) == ["a", "b", "c"]


def test_get_all_keys_after_cleanup():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("a", now=100.0)
    rl.is_allowed("b", now=100.0)
    rl.cleanup_expired(now=400.0)
    assert rl.get_all_keys() == []


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def test_create_rate_limiter_60_rpm():
    rl = create_rate_limiter(requests_per_minute=60)
    assert rl.max_tokens == 60
    assert rl.refill_rate == pytest.approx(1.0)
    assert rl.window_seconds == 60.0


def test_create_rate_limiter_allows_up_to_limit():
    rl = create_rate_limiter(requests_per_minute=3)
    assert rl.is_allowed("u", now=100.0) is True
    assert rl.is_allowed("u", now=100.0) is True
    assert rl.is_allowed("u", now=100.0) is True
    assert rl.is_allowed("u", now=100.0) is False


def test_create_burst_limiter_configuration():
    rl = create_burst_limiter(burst_size=10, sustained_per_second=2.0)
    assert rl.max_tokens == 10
    assert rl.refill_rate == 2.0
    assert rl.window_seconds == 1.0


def test_create_burst_limiter_allows_burst_then_throttles():
    rl = create_burst_limiter(burst_size=5, sustained_per_second=1.0)
    # All 5 burst requests allowed at t=0
    for _ in range(5):
        assert rl.is_allowed("u", now=0.0) is True
    assert rl.is_allowed("u", now=0.0) is False
    # After 3 seconds, 3 tokens refilled
    for _ in range(3):
        assert rl.is_allowed("u", now=3.0) is True
    assert rl.is_allowed("u", now=3.0) is False


# ---------------------------------------------------------------------------
# Concurrency / ordering edge cases
# ---------------------------------------------------------------------------

def test_monotonically_increasing_timestamps_tracked():
    rl = RateLimiter(max_tokens=10, refill_rate=1.0)
    rl.is_allowed("user1", now=100.0)
    rl.is_allowed("user1", now=101.0)
    rl.is_allowed("user1", now=102.0)
    status = rl.get_remaining("user1", now=102.0)
    assert status["requests_in_window"] == 3


def test_time_going_backwards_does_not_refill():
    """_refill guards against elapsed <= 0, so backwards time is a no-op."""
    rl = RateLimiter(max_tokens=5, refill_rate=10.0)
    rl.is_allowed("user1", now=100.0)  # 4 tokens left
    # Passing an earlier timestamp should not refill
    status = rl.get_remaining("user1", now=99.0)
    # Since elapsed = 99 - 100 = -1 <= 0, refill is skipped; still 4 tokens
    assert status["remaining_tokens"] == 4.0


def test_very_large_elapsed_time_caps_at_max():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    rl.is_allowed("user1", now=0.0)  # 4 tokens left
    # After 1 million seconds, still capped at 5
    status = rl.get_remaining("user1", now=1_000_000.0)
    assert status["remaining_tokens"] == 5.0
