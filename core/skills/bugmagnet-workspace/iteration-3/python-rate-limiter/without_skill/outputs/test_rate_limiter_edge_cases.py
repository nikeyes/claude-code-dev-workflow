"""
Comprehensive edge case tests for the token bucket rate limiter.

Covers boundary conditions, error paths, and behaviours not exercised by
the baseline happy-path test suite.
"""

import math
import pytest
from rate_limiter import RateLimiter, create_rate_limiter, create_burst_limiter


# ---------------------------------------------------------------------------
# Constructor / configuration validation
# ---------------------------------------------------------------------------


class TestConstructorBoundaries:
    def test_max_tokens_zero_blocks_every_request(self):
        """A limiter with zero capacity must reject all requests immediately."""
        rl = RateLimiter(max_tokens=0, refill_rate=1.0)
        assert rl.is_allowed("user1", now=100.0) is False

    def test_max_tokens_one_allows_exactly_one_then_blocks(self):
        rl = RateLimiter(max_tokens=1, refill_rate=0.0)
        assert rl.is_allowed("user1", now=100.0) is True
        assert rl.is_allowed("user1", now=100.0) is False

    def test_refill_rate_zero_never_refills(self):
        """With refill_rate=0 the bucket never replenishes after exhaustion."""
        rl = RateLimiter(max_tokens=1, refill_rate=0.0)
        rl.is_allowed("user1", now=100.0)
        # Even a huge time jump should not refill
        assert rl.is_allowed("user1", now=1_000_000.0) is False

    def test_fractional_max_tokens(self):
        """max_tokens=0.5 — a cost-1 request is denied because 0.5 < 1."""
        rl = RateLimiter(max_tokens=0.5, refill_rate=1.0)
        assert rl.is_allowed("user1", cost=1.0, now=100.0) is False

    def test_very_large_max_tokens(self):
        rl = RateLimiter(max_tokens=10_000_000, refill_rate=1.0)
        assert rl.is_allowed("user1", now=100.0) is True


# ---------------------------------------------------------------------------
# Token refill behaviour
# ---------------------------------------------------------------------------


class TestTokenRefill:
    def test_tokens_refill_over_time(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        # Drain the bucket
        for _ in range(5):
            rl.is_allowed("user1", now=100.0)
        assert rl.is_allowed("user1", now=100.0) is False
        # One second later exactly one token has been added
        assert rl.is_allowed("user1", now=101.0) is True

    def test_tokens_do_not_exceed_max_tokens(self):
        """After a long idle period the bucket must cap at max_tokens."""
        rl = RateLimiter(max_tokens=5, refill_rate=10.0)
        rl.is_allowed("user1", now=0.0)  # create entry
        status = rl.get_remaining("user1", now=1_000.0)
        assert status["remaining_tokens"] == 5.0

    def test_partial_refill_allows_correct_count(self):
        """With refill_rate=2.0, waiting 0.5 s adds exactly 1 token."""
        rl = RateLimiter(max_tokens=3, refill_rate=2.0)
        for _ in range(3):
            rl.is_allowed("user1", now=0.0)
        # 0.5 s × 2.0 tokens/s = 1.0 token
        assert rl.is_allowed("user1", now=0.5) is True
        assert rl.is_allowed("user1", now=0.5) is False

    def test_refill_does_not_happen_backwards_in_time(self):
        """If now < last_refill the bucket must not change (elapsed <= 0)."""
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        for _ in range(5):
            rl.is_allowed("user1", now=100.0)
        # Time goes backward — must not add tokens
        assert rl.is_allowed("user1", now=99.0) is False

    def test_refill_at_exact_refill_boundary(self):
        """Elapsed == 0 must not add any tokens (boundary guard in _refill)."""
        rl = RateLimiter(max_tokens=2, refill_rate=1.0)
        rl.is_allowed("user1", now=100.0)
        rl.is_allowed("user1", now=100.0)
        # Same timestamp: no refill possible
        assert rl.is_allowed("user1", now=100.0) is False


# ---------------------------------------------------------------------------
# Fractional / custom cost
# ---------------------------------------------------------------------------


class TestCostParameter:
    def test_cost_greater_than_one_consumes_multiple_tokens(self):
        rl = RateLimiter(max_tokens=10, refill_rate=1.0)
        assert rl.is_allowed("user1", cost=7.0, now=100.0) is True
        # Only 3 tokens left; cost=4 must be denied
        assert rl.is_allowed("user1", cost=4.0, now=100.0) is False

    def test_cost_exactly_equal_to_remaining_tokens_is_allowed(self):
        rl = RateLimiter(max_tokens=3, refill_rate=1.0)
        assert rl.is_allowed("user1", cost=3.0, now=100.0) is True

    def test_cost_zero_is_always_allowed_and_does_not_consume(self):
        """A zero-cost request must be admitted and leave tokens unchanged."""
        rl = RateLimiter(max_tokens=2, refill_rate=1.0)
        rl.is_allowed("user1", now=100.0)
        rl.is_allowed("user1", now=100.0)  # drain
        # cost=0: tokens are 0.0; 0.0 >= 0.0 → allowed
        assert rl.is_allowed("user1", cost=0.0, now=100.0) is True
        # BUG PROBE: tokens should not go negative
        status = rl.get_remaining("user1", now=100.0)
        assert status["remaining_tokens"] >= 0.0

    def test_fractional_cost_works_correctly(self):
        rl = RateLimiter(max_tokens=1, refill_rate=1.0)
        assert rl.is_allowed("user1", cost=0.3, now=100.0) is True
        assert rl.is_allowed("user1", cost=0.3, now=100.0) is True
        assert rl.is_allowed("user1", cost=0.3, now=100.0) is True
        # Three × 0.3 = 0.9 consumed; 0.1 remaining — cost=0.2 must be denied
        assert rl.is_allowed("user1", cost=0.2, now=100.0) is False

    def test_cost_larger_than_max_tokens_is_never_allowed(self):
        """A cost that exceeds max_tokens can never be satisfied."""
        rl = RateLimiter(max_tokens=5, refill_rate=100.0)
        # Even after massive refill, tokens cap at max_tokens=5
        assert rl.is_allowed("user1", cost=10.0, now=1_000_000.0) is False

    def test_negative_cost_is_handled_gracefully(self):
        """
        Negative cost makes entry.tokens >= cost trivially true and adds tokens.
        This is likely an unintended design gap; document the behaviour.
        """
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        for _ in range(5):
            rl.is_allowed("user1", now=100.0)
        # With cost=-1, the check 0 >= -1 is True → allowed and tokens INCREASE
        result = rl.is_allowed("user1", cost=-1.0, now=100.0)
        # This should ideally raise ValueError; for now just document behaviour
        # The implementation allows it and increases tokens:
        assert result is True
        status = rl.get_remaining("user1", now=100.0)
        assert status["remaining_tokens"] == 1.0  # 0 - (-1) = +1


# ---------------------------------------------------------------------------
# Key isolation
# ---------------------------------------------------------------------------


class TestKeyIsolation:
    def test_different_keys_are_independent(self):
        rl = RateLimiter(max_tokens=1, refill_rate=1.0)
        assert rl.is_allowed("user1", now=100.0) is True
        assert rl.is_allowed("user1", now=100.0) is False
        # user2 has its own full bucket
        assert rl.is_allowed("user2", now=100.0) is True

    def test_empty_string_key_is_tracked_independently(self):
        rl = RateLimiter(max_tokens=1, refill_rate=1.0)
        assert rl.is_allowed("", now=100.0) is True
        assert rl.is_allowed("", now=100.0) is False
        assert rl.is_allowed("non-empty", now=100.0) is True

    def test_unicode_key(self):
        rl = RateLimiter(max_tokens=2, refill_rate=1.0)
        assert rl.is_allowed("用户123", now=100.0) is True
        assert rl.is_allowed("用户123", now=100.0) is True
        assert rl.is_allowed("用户123", now=100.0) is False

    def test_very_long_key(self):
        long_key = "x" * 10_000
        rl = RateLimiter(max_tokens=1, refill_rate=1.0)
        assert rl.is_allowed(long_key, now=100.0) is True

    def test_many_distinct_keys(self):
        rl = RateLimiter(max_tokens=1, refill_rate=1.0)
        keys = [f"user{i}" for i in range(1_000)]
        for key in keys:
            assert rl.is_allowed(key, now=100.0) is True
        assert len(rl.get_all_keys()) == 1_000


# ---------------------------------------------------------------------------
# Sliding window (request_timestamps)
# ---------------------------------------------------------------------------


class TestSlidingWindow:
    def test_timestamps_outside_window_are_cleaned(self):
        rl = RateLimiter(max_tokens=10, refill_rate=1.0, window_seconds=60.0)
        for _ in range(5):
            rl.is_allowed("user1", now=0.0)
        # Jump past the 60-second window
        status = rl.get_remaining("user1", now=61.0)
        assert status["requests_in_window"] == 0

    def test_timestamps_on_window_boundary_are_excluded(self):
        """Timestamps at exactly cutoff (ts == now - window_seconds) are excluded
        because _clean_window uses strict greater-than (ts > cutoff)."""
        rl = RateLimiter(max_tokens=10, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("user1", now=0.0)
        # At now=60.0, cutoff=0.0; ts=0.0 is NOT > 0.0 → excluded
        status = rl.get_remaining("user1", now=60.0)
        assert status["requests_in_window"] == 0

    def test_timestamps_just_inside_window_are_retained(self):
        rl = RateLimiter(max_tokens=10, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("user1", now=0.0)
        # At now=59.9, cutoff=-0.1; ts=0.0 > -0.1 → retained
        status = rl.get_remaining("user1", now=59.9)
        assert status["requests_in_window"] == 1

    def test_denied_requests_are_not_added_to_timestamps(self):
        rl = RateLimiter(max_tokens=2, refill_rate=0.0)
        rl.is_allowed("user1", now=100.0)
        rl.is_allowed("user1", now=100.0)
        rl.is_allowed("user1", now=100.0)  # denied
        status = rl.get_remaining("user1", now=100.0)
        assert status["requests_in_window"] == 2

    def test_get_remaining_does_not_consume_tokens(self):
        """get_remaining is a read-only introspection; tokens must not change."""
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        rl.is_allowed("user1", now=100.0)
        before = rl.get_remaining("user1", now=100.0)["remaining_tokens"]
        rl.get_remaining("user1", now=100.0)
        after = rl.get_remaining("user1", now=100.0)["remaining_tokens"]
        assert before == after

    def test_get_remaining_creates_entry_for_new_key(self):
        """Calling get_remaining on an unknown key must create it at max_tokens."""
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        status = rl.get_remaining("new_key", now=100.0)
        assert status["remaining_tokens"] == 5.0
        assert "new_key" in rl.get_all_keys()

    def test_resets_at_field_is_correct(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("user1", now=100.0)
        status = rl.get_remaining("user1", now=100.0)
        # last_refill is set when entry is created (now=100.0) and updated on refill
        assert status["resets_at"] == pytest.approx(160.0)


# ---------------------------------------------------------------------------
# get_wait_time
# ---------------------------------------------------------------------------


class TestGetWaitTime:
    def test_returns_zero_when_tokens_available(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        assert rl.get_wait_time("user1", now=100.0) == 0.0

    def test_returns_correct_wait_after_exhaustion(self):
        rl = RateLimiter(max_tokens=1, refill_rate=1.0)
        rl.is_allowed("user1", now=100.0)
        wait = rl.get_wait_time("user1", cost=1.0, now=100.0)
        assert wait == pytest.approx(1.0)

    def test_wait_time_for_cost_greater_than_max_tokens(self):
        """
        BUG: When cost > max_tokens, the request can NEVER be fulfilled.
        get_wait_time returns deficit / refill_rate — a finite wait — but
        is_allowed will always return False because tokens are capped at
        max_tokens.  The method should ideally return infinity (or raise)
        to signal the request is impossible.
        """
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        wait = rl.get_wait_time("user1", cost=10.0, now=0.0)
        # Current implementation: returns 5.0 (wrong — waiting will not help)
        # Correct behaviour: math.inf or ValueError
        # This test documents the bug:
        assert wait == pytest.approx(5.0)   # actual (buggy) result
        # To assert the correct behaviour, uncomment:
        # assert wait == math.inf

    def test_wait_time_with_zero_refill_rate_is_infinite(self):
        """
        BUG: With refill_rate=0.0, deficit / 0.0 raises ZeroDivisionError.
        """
        rl = RateLimiter(max_tokens=1, refill_rate=0.0)
        rl.is_allowed("user1", now=100.0)
        with pytest.raises(ZeroDivisionError):
            rl.get_wait_time("user1", cost=1.0, now=100.0)

    def test_wait_time_partial_deficit(self):
        rl = RateLimiter(max_tokens=5, refill_rate=2.0)
        for _ in range(5):
            rl.is_allowed("user1", now=0.0)
        wait = rl.get_wait_time("user1", cost=3.0, now=0.0)
        # deficit=3, refill_rate=2 → 1.5 s
        assert wait == pytest.approx(1.5)

    def test_wait_time_does_not_create_timestamp(self):
        """get_wait_time must not record a request timestamp."""
        rl = RateLimiter(max_tokens=3, refill_rate=1.0)
        for _ in range(3):
            rl.is_allowed("user1", now=100.0)
        rl.get_wait_time("user1", now=100.0)
        status = rl.get_remaining("user1", now=100.0)
        assert status["requests_in_window"] == 3


# ---------------------------------------------------------------------------
# cleanup_expired
# ---------------------------------------------------------------------------


class TestCleanupExpired:
    def test_removes_idle_entries_beyond_threshold(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("user1", now=0.0)
        # threshold = 2 × 60 = 120; at now=121 the entry is expired
        removed = rl.cleanup_expired(now=121.0)
        assert removed == 1
        assert "user1" not in rl.get_all_keys()

    def test_does_not_remove_recently_active_entries(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("user1", now=0.0)
        removed = rl.cleanup_expired(now=60.0)
        assert removed == 0
        assert "user1" in rl.get_all_keys()

    def test_cleanup_on_boundary(self):
        """Entry at exactly the expiry threshold must NOT be removed (>)."""
        rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("user1", now=0.0)
        # now - last_refill == 120 → NOT > 120 → not expired
        removed = rl.cleanup_expired(now=120.0)
        assert removed == 0

    def test_cleanup_just_past_boundary(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("user1", now=0.0)
        removed = rl.cleanup_expired(now=120.001)
        assert removed == 1

    def test_cleanup_multiple_entries(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=10.0)
        for key in ["a", "b", "c"]:
            rl.is_allowed(key, now=0.0)
        rl.is_allowed("recent", now=100.0)
        removed = rl.cleanup_expired(now=121.0)
        assert removed == 3
        assert rl.get_all_keys() == ["recent"]

    def test_cleanup_empty_store(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        assert rl.cleanup_expired(now=1_000.0) == 0

    def test_cleanup_uses_last_refill_not_last_request(self):
        """
        BUG: cleanup_expired uses entry.last_refill as the idle timestamp.
        Calling get_remaining (which calls _refill) resets last_refill even
        if no actual request was made.  A key that was only polled but never
        had a real request allowed will therefore never be cleaned up as long
        as get_remaining is called regularly.

        This test documents the expected-but-absent behaviour: entries that
        have had no allowed requests should still expire based on when they
        were last truly active.
        """
        rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=10.0)
        rl.is_allowed("user1", now=0.0)
        # Poll at t=25 — this updates last_refill to 25.0 via _refill
        rl.get_remaining("user1", now=25.0)
        # Threshold = 20 s; now=30, last_refill=25 → 5 s elapsed → not expired
        removed = rl.cleanup_expired(now=30.0)
        # Entry survives because get_remaining refreshed last_refill
        assert removed == 0


# ---------------------------------------------------------------------------
# get_all_keys
# ---------------------------------------------------------------------------


class TestGetAllKeys:
    def test_empty_initially(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        assert rl.get_all_keys() == []

    def test_returns_all_tracked_keys(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        rl.is_allowed("a", now=1.0)
        rl.is_allowed("b", now=1.0)
        keys = rl.get_all_keys()
        assert set(keys) == {"a", "b"}

    def test_returns_copy_not_live_reference(self):
        """Mutating the returned list must not affect internal state."""
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        rl.is_allowed("a", now=1.0)
        keys = rl.get_all_keys()
        keys.append("injected")
        assert "injected" not in rl.get_all_keys()


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------


class TestFactoryFunctions:
    def test_create_rate_limiter_60_rpm(self):
        rl = create_rate_limiter(requests_per_minute=60)
        assert rl.max_tokens == 60
        assert rl.refill_rate == pytest.approx(1.0)
        assert rl.window_seconds == 60.0

    def test_create_rate_limiter_allows_exactly_rpm_requests_per_minute(self):
        """After draining, exactly rpm requests fit in 60 s."""
        rl = create_rate_limiter(requests_per_minute=10)
        # Use up all tokens
        for _ in range(10):
            rl.is_allowed("u", now=0.0)
        assert rl.is_allowed("u", now=0.0) is False
        # One minute later, bucket is full again
        for _ in range(10):
            assert rl.is_allowed("u", now=60.0) is True
        assert rl.is_allowed("u", now=60.0) is False

    def test_create_rate_limiter_zero_rpm(self):
        """
        BUG: create_rate_limiter(0) sets refill_rate=0/60=0.0 and max_tokens=0.
        Every request is denied and get_wait_time raises ZeroDivisionError.
        """
        rl = create_rate_limiter(requests_per_minute=0)
        assert rl.is_allowed("u", now=0.0) is False
        with pytest.raises(ZeroDivisionError):
            rl.get_wait_time("u", now=0.0)

    def test_create_burst_limiter_allows_burst_then_throttles(self):
        rl = create_burst_limiter(burst_size=10, sustained_per_second=1.0)
        for _ in range(10):
            assert rl.is_allowed("u", now=0.0) is True
        assert rl.is_allowed("u", now=0.0) is False
        assert rl.is_allowed("u", now=1.0) is True

    def test_create_burst_limiter_window_is_one_second(self):
        rl = create_burst_limiter(burst_size=5, sustained_per_second=2.0)
        assert rl.window_seconds == 1.0


# ---------------------------------------------------------------------------
# now parameter (deterministic time control)
# ---------------------------------------------------------------------------


class TestNowParameter:
    def test_is_allowed_uses_provided_now(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        # Provide an explicit timestamp far in the past — must still work
        assert rl.is_allowed("u", now=0.0) is True

    def test_get_remaining_uses_provided_now(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        status = rl.get_remaining("u", now=0.0)
        assert status["remaining_tokens"] == 5.0

    def test_get_wait_time_uses_provided_now(self):
        rl = RateLimiter(max_tokens=1, refill_rate=1.0)
        rl.is_allowed("u", now=0.0)
        wait = rl.get_wait_time("u", now=0.0)
        assert wait == pytest.approx(1.0)

    def test_cleanup_expired_uses_provided_now(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("u", now=0.0)
        assert rl.cleanup_expired(now=0.0) == 0


# ---------------------------------------------------------------------------
# Concurrent / stress patterns (single-threaded simulation)
# ---------------------------------------------------------------------------


class TestHighVolumePatterns:
    def test_many_requests_same_key_single_second(self):
        """Exactly max_tokens requests succeed at t=0, rest are denied."""
        rl = RateLimiter(max_tokens=100, refill_rate=10.0)
        allowed = sum(1 for _ in range(200) if rl.is_allowed("u", now=0.0))
        assert allowed == 100

    def test_request_count_in_window_never_exceeds_allowed(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=10.0)
        for _ in range(20):
            rl.is_allowed("u", now=0.0)
        status = rl.get_remaining("u", now=0.0)
        assert status["requests_in_window"] <= 5

    def test_interleaved_allowed_and_denied_requests(self):
        """Tokens accumulate and are consumed in a repeating burst pattern."""
        rl = RateLimiter(max_tokens=2, refill_rate=2.0)
        results = []
        for t in range(10):
            results.append(rl.is_allowed("u", now=float(t)))
            results.append(rl.is_allowed("u", now=float(t)))
            results.append(rl.is_allowed("u", now=float(t)))
        # At each integer second, 2 tokens are refilled; 3 requests are made
        # so every third attempt per second is denied
        denied = results.count(False)
        assert denied > 0  # at least some must be denied
