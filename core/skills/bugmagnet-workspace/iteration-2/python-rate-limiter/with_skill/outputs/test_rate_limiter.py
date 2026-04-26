"""Tests for the rate limiter — happy path and edge cases."""

import pytest
from rate_limiter import RateLimiter, create_rate_limiter, create_burst_limiter


# ---------------------------------------------------------------------------
# Baseline tests (original)
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
# Token refill behavior
# ---------------------------------------------------------------------------

def test_allows_request_after_tokens_refill():
    rl = RateLimiter(max_tokens=1, refill_rate=1.0)
    assert rl.is_allowed("user1", now=100.0) is True   # consumes last token
    assert rl.is_allowed("user1", now=100.0) is False  # no tokens
    assert rl.is_allowed("user1", now=101.0) is True   # 1 token refilled


def test_refill_does_not_exceed_max_tokens():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    rl.is_allowed("user1", now=100.0)  # 4 tokens remain
    status = rl.get_remaining("user1", now=200.0)  # 100 s elapsed → would add 100 tokens
    assert status["remaining_tokens"] == 5.0  # capped at max


def test_partial_refill_restores_correct_number_of_tokens():
    rl = RateLimiter(max_tokens=10, refill_rate=2.0)
    # exhaust all tokens
    for _ in range(10):
        rl.is_allowed("user1", now=100.0)
    # 3 seconds later → 6 tokens refilled
    status = rl.get_remaining("user1", now=103.0)
    assert status["remaining_tokens"] == 6.0


# ---------------------------------------------------------------------------
# Independent keys
# ---------------------------------------------------------------------------

def test_different_keys_are_rate_limited_independently():
    rl = RateLimiter(max_tokens=1, refill_rate=1.0)
    assert rl.is_allowed("user1", now=100.0) is True
    assert rl.is_allowed("user2", now=100.0) is True  # separate bucket


def test_exhausting_one_key_does_not_affect_another_key():
    rl = RateLimiter(max_tokens=1, refill_rate=1.0)
    rl.is_allowed("user1", now=100.0)  # exhaust user1
    assert rl.is_allowed("user1", now=100.0) is False
    assert rl.is_allowed("user2", now=100.0) is True


# ---------------------------------------------------------------------------
# is_allowed — cost parameter
# ---------------------------------------------------------------------------

def test_allows_request_when_cost_equals_remaining_tokens_exactly():
    rl = RateLimiter(max_tokens=3, refill_rate=1.0)
    assert rl.is_allowed("user1", cost=3.0, now=100.0) is True


def test_blocks_request_when_cost_exceeds_remaining_tokens_by_tiny_amount():
    rl = RateLimiter(max_tokens=3, refill_rate=1.0)
    assert rl.is_allowed("user1", cost=3.0001, now=100.0) is False


def test_allows_request_with_fractional_cost():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    assert rl.is_allowed("user1", cost=0.5, now=100.0) is True
    status = rl.get_remaining("user1", now=100.0)
    assert status["remaining_tokens"] == 4.5


def test_blocks_when_cost_greater_than_max_tokens():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    # cost exceeds bucket capacity — can never be satisfied
    assert rl.is_allowed("user1", cost=10.0, now=100.0) is False


# ---------------------------------------------------------------------------
# is_allowed — request_timestamps tracking
# ---------------------------------------------------------------------------

def test_allowed_request_is_recorded_in_window():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("user1", now=100.0)
    rl.is_allowed("user1", now=110.0)
    status = rl.get_remaining("user1", now=120.0)
    assert status["requests_in_window"] == 2


def test_denied_request_is_not_recorded_in_window():
    rl = RateLimiter(max_tokens=1, refill_rate=0.1)
    rl.is_allowed("user1", now=100.0)  # allowed
    rl.is_allowed("user1", now=100.0)  # denied
    status = rl.get_remaining("user1", now=100.0)
    assert status["requests_in_window"] == 1


def test_requests_outside_sliding_window_are_not_counted():
    rl = RateLimiter(max_tokens=10, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("user1", now=100.0)  # will be outside window at now=161
    rl.is_allowed("user1", now=130.0)  # will be inside window at now=161
    status = rl.get_remaining("user1", now=161.0)
    assert status["requests_in_window"] == 1


def test_request_at_exact_window_cutoff_is_excluded_from_count():
    """Timestamps exactly at the cutoff boundary (now - window_seconds) are excluded.

    _clean_window uses strict > comparison, so ts == cutoff is dropped.
    """
    rl = RateLimiter(max_tokens=10, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("user1", now=100.0)  # ts=100.0; cutoff at now=160.0 is also 100.0
    status = rl.get_remaining("user1", now=160.0)
    assert status["requests_in_window"] == 0


# ---------------------------------------------------------------------------
# get_remaining — full structure
# ---------------------------------------------------------------------------

def test_get_remaining_returns_all_required_fields():
    rl = RateLimiter(max_tokens=10, refill_rate=1.0, window_seconds=60.0)
    status = rl.get_remaining("user1", now=100.0)
    assert set(status.keys()) == {"remaining_tokens", "requests_in_window", "window_seconds", "resets_at"}


def test_get_remaining_for_new_key_shows_full_tokens():
    rl = RateLimiter(max_tokens=10, refill_rate=1.0)
    status = rl.get_remaining("newuser", now=100.0)
    assert status["remaining_tokens"] == 10.0
    assert status["requests_in_window"] == 0


def test_get_remaining_resets_at_is_last_refill_plus_window():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("user1", now=100.0)
    status = rl.get_remaining("user1", now=100.0)
    assert status["resets_at"] == 160.0


def test_get_remaining_does_not_consume_tokens():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    rl.get_remaining("user1", now=100.0)
    rl.get_remaining("user1", now=100.0)
    status = rl.get_remaining("user1", now=100.0)
    assert status["remaining_tokens"] == 5.0


def test_get_remaining_window_seconds_matches_constructor():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=30.0)
    status = rl.get_remaining("user1", now=100.0)
    assert status["window_seconds"] == 30.0


# ---------------------------------------------------------------------------
# get_wait_time
# ---------------------------------------------------------------------------

def test_get_wait_time_returns_zero_when_tokens_are_available():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    assert rl.get_wait_time("user1", now=100.0) == 0.0


def test_get_wait_time_returns_zero_for_new_key():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    assert rl.get_wait_time("brand_new", now=100.0) == 0.0


def test_get_wait_time_returns_correct_seconds_when_tokens_exhausted():
    rl = RateLimiter(max_tokens=2, refill_rate=1.0)
    rl.is_allowed("user1", now=100.0)
    rl.is_allowed("user1", now=100.0)
    # 0 tokens left; need 1 token at rate=1.0 → wait 1 second
    wait = rl.get_wait_time("user1", now=100.0)
    assert wait == pytest.approx(1.0)


def test_get_wait_time_accounts_for_high_cost():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    rl.is_allowed("user1", cost=4.0, now=100.0)  # 1 token remains
    # need 3 more tokens at rate=1.0 → wait 2 seconds
    wait = rl.get_wait_time("user1", cost=3.0, now=100.0)
    assert wait == pytest.approx(2.0)


def test_get_wait_time_does_not_consume_tokens():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    rl.get_wait_time("user1", now=100.0)
    rl.get_wait_time("user1", now=100.0)
    status = rl.get_remaining("user1", now=100.0)
    assert status["remaining_tokens"] == 5.0


def test_get_wait_time_returns_zero_when_cost_equals_remaining_exactly():
    rl = RateLimiter(max_tokens=3, refill_rate=1.0)
    wait = rl.get_wait_time("user1", cost=3.0, now=100.0)
    assert wait == 0.0


# ---------------------------------------------------------------------------
# cleanup_expired
# ---------------------------------------------------------------------------

def test_cleanup_expired_returns_zero_when_no_entries():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    assert rl.cleanup_expired(now=100.0) == 0


def test_cleanup_expired_removes_entries_idle_longer_than_twice_window():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("user1", now=100.0)
    # threshold = 120 s; now=221.0 → idle 121 s > 120 s → should be removed
    count = rl.cleanup_expired(now=221.0)
    assert count == 1
    assert "user1" not in rl.get_all_keys()


def test_cleanup_expired_keeps_entries_idle_less_than_twice_window():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("user1", now=100.0)
    # threshold = 120 s; now=219.0 → idle 119 s < 120 s → should stay
    count = rl.cleanup_expired(now=219.0)
    assert count == 0
    assert "user1" in rl.get_all_keys()


def test_cleanup_expired_removes_only_idle_entries_among_multiple_keys():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("old_user", now=100.0)
    rl.is_allowed("active_user", now=300.0)
    # at now=350: old_user idle 250 s > 120 s → removed; active_user idle 50 s < 120 s → kept
    count = rl.cleanup_expired(now=350.0)
    assert count == 1
    assert "old_user" not in rl.get_all_keys()
    assert "active_user" in rl.get_all_keys()


def test_cleanup_expired_returns_count_of_removed_entries():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("user1", now=100.0)
    rl.is_allowed("user2", now=100.0)
    rl.is_allowed("user3", now=100.0)
    count = rl.cleanup_expired(now=400.0)
    assert count == 3


# ---------------------------------------------------------------------------
# get_all_keys
# ---------------------------------------------------------------------------

def test_get_all_keys_returns_empty_list_initially():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    assert rl.get_all_keys() == []


def test_get_all_keys_returns_keys_after_requests():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0)
    rl.is_allowed("user1", now=100.0)
    rl.is_allowed("user2", now=100.0)
    keys = rl.get_all_keys()
    assert sorted(keys) == ["user1", "user2"]


def test_get_all_keys_does_not_include_key_after_cleanup():
    rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
    rl.is_allowed("user1", now=100.0)
    rl.cleanup_expired(now=400.0)
    assert rl.get_all_keys() == []


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def test_create_rate_limiter_allows_up_to_requests_per_minute():
    rl = create_rate_limiter(requests_per_minute=60)
    assert rl.max_tokens == 60
    assert rl.refill_rate == pytest.approx(1.0)  # 60/60
    assert rl.window_seconds == 60.0


def test_create_rate_limiter_blocks_after_limit_reached():
    rl = create_rate_limiter(requests_per_minute=2)
    assert rl.is_allowed("user1", now=100.0) is True
    assert rl.is_allowed("user1", now=100.0) is True
    assert rl.is_allowed("user1", now=100.0) is False


def test_create_burst_limiter_configures_correct_parameters():
    rl = create_burst_limiter(burst_size=10, sustained_per_second=2.0)
    assert rl.max_tokens == 10
    assert rl.refill_rate == 2.0
    assert rl.window_seconds == 1.0


def test_create_burst_limiter_allows_burst_then_throttles():
    rl = create_burst_limiter(burst_size=3, sustained_per_second=1.0)
    assert rl.is_allowed("user1", now=100.0) is True
    assert rl.is_allowed("user1", now=100.0) is True
    assert rl.is_allowed("user1", now=100.0) is True
    assert rl.is_allowed("user1", now=100.0) is False   # burst exhausted
    assert rl.is_allowed("user1", now=101.0) is True    # 1 token refilled


# ---------------------------------------------------------------------------
# Phase 4: bugmagnet session 2026-04-26
# ---------------------------------------------------------------------------

class TestBugmagnetSession20260426:
    """Exploratory edge cases and bug cluster tests."""

    # --- Numeric edge cases: zero / negative cost ---

    def test_returns_true_when_cost_is_zero(self):
        """Zero cost is always allowed (0 >= 0); appends a timestamp."""
        rl = RateLimiter(max_tokens=0, refill_rate=1.0)
        # Even a bucket with 0 tokens should allow zero-cost requests
        assert rl.is_allowed("user1", cost=0.0, now=100.0) is True

    def test_tokens_not_decreased_below_zero_when_cost_is_zero(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        rl.is_allowed("user1", cost=0.0, now=100.0)
        status = rl.get_remaining("user1", now=100.0)
        assert status["remaining_tokens"] == 5.0

    def test_get_wait_time_returns_zero_when_cost_is_zero(self):
        rl = RateLimiter(max_tokens=0, refill_rate=1.0)
        assert rl.get_wait_time("user1", cost=0.0, now=100.0) == 0.0

    @pytest.mark.skip(reason="BUG: negative cost increases token balance above max_tokens")
    def test_negative_cost_does_not_increase_token_balance_BUG(self):
        """
        BUG: Negative cost causes is_allowed to ADD tokens to the bucket.

        ROOT CAUSE: is_allowed checks `entry.tokens >= cost` which is True when cost is
        negative (any non-negative token balance >= any negative number).  Then it
        executes `entry.tokens -= cost` which ADDS the absolute value to tokens, pushing
        the balance above max_tokens.

        CODE LOCATION: rate_limiter.py:62
            entry.tokens -= cost   # with cost=-1.0 this becomes tokens += 1.0

        PROPOSED FIX: Validate that cost > 0 (or >= 0) at the entry point of is_allowed
        and get_wait_time, e.g.:
            if cost < 0:
                raise ValueError(f"cost must be non-negative, got {cost}")

        EXPECTED: ValueError or False returned for negative cost
        ACTUAL:   Tokens are increased; balance can exceed max_tokens
        """
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        rl.is_allowed("user1", cost=-1.0, now=100.0)
        status = rl.get_remaining("user1", now=100.0)
        assert status["remaining_tokens"] == 5.0  # should not exceed max_tokens
        # Actual: remaining_tokens == 6.0

    @pytest.mark.skip(reason="BUG: get_wait_time raises ZeroDivisionError when refill_rate=0")
    def test_get_wait_time_with_zero_refill_rate_raises_meaningful_error_BUG(self):
        """
        BUG: get_wait_time raises ZeroDivisionError when refill_rate=0 and
        tokens are insufficient.

        ROOT CAUSE: rate_limiter.py:81
            return deficit / self.refill_rate
        When refill_rate=0, this is a division by zero.

        PROPOSED FIX: Guard against zero refill rate, e.g.:
            if self.refill_rate == 0:
                return float('inf')  # will never refill

        EXPECTED: Returns float('inf') or raises a descriptive ValueError
        ACTUAL:   Raises ZeroDivisionError
        """
        rl = RateLimiter(max_tokens=1, refill_rate=0.0)
        rl.is_allowed("user1", now=100.0)  # exhaust the one token
        wait = rl.get_wait_time("user1", now=100.0)  # ZeroDivisionError here
        assert wait == float("inf")

    # --- Stateful operations ---

    def test_get_wait_time_side_effect_creates_entry_for_new_key(self):
        """get_wait_time creates an entry for a key that did not exist before."""
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        rl.get_wait_time("newkey", now=100.0)
        assert "newkey" in rl.get_all_keys()

    def test_get_remaining_side_effect_creates_entry_for_new_key(self):
        """get_remaining creates an entry for a key that did not exist before."""
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        rl.get_remaining("newkey", now=100.0)
        assert "newkey" in rl.get_all_keys()

    def test_repeated_is_allowed_calls_accumulate_correctly(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        results = [rl.is_allowed("user1", now=100.0) for _ in range(7)]
        assert results == [True, True, True, True, True, False, False]

    def test_is_allowed_after_cleanup_creates_fresh_entry(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("user1", now=100.0)
        rl.cleanup_expired(now=400.0)
        # Entry is gone; next call creates a fresh one with full tokens
        assert rl.is_allowed("user1", now=400.0) is True
        status = rl.get_remaining("user1", now=400.0)
        assert status["remaining_tokens"] == 4.0

    # --- Token refill precision ---

    def test_tokens_refill_proportionally_to_elapsed_time(self):
        rl = RateLimiter(max_tokens=10, refill_rate=0.5)
        for _ in range(10):
            rl.is_allowed("user1", now=100.0)
        # 4 seconds at 0.5 tokens/s → 2 tokens
        status = rl.get_remaining("user1", now=104.0)
        assert status["remaining_tokens"] == pytest.approx(2.0)

    def test_refill_does_not_occur_when_time_goes_backward(self):
        """_refill guards against elapsed <= 0; negative elapsed is ignored."""
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        rl.is_allowed("user1", now=100.0)   # 4 tokens left
        # Attempt with earlier timestamp (simulated clock skew)
        rl.is_allowed("user1", now=99.0)    # elapsed <= 0 → no refill; still 3 tokens
        status = rl.get_remaining("user1", now=99.0)
        assert status["remaining_tokens"] == 3.0

    # --- Sliding window boundary precision ---

    def test_requests_one_second_after_window_cutoff_are_still_counted(self):
        rl = RateLimiter(max_tokens=10, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("user1", now=100.0)
        # now=159.0 → cutoff=99.0; ts=100.0 > 99.0 → still inside window
        status = rl.get_remaining("user1", now=159.0)
        assert status["requests_in_window"] == 1

    # --- Very large cost ---

    def test_blocks_immediately_when_cost_exceeds_max_tokens_permanently(self):
        """A cost larger than max_tokens can never be satisfied."""
        rl = RateLimiter(max_tokens=5, refill_rate=100.0)
        # Even with rapid refill rate, cost=1000 > max_tokens=5 → always denied
        assert rl.is_allowed("user1", cost=1000.0, now=100.0) is False

    def test_get_wait_time_for_cost_exceeding_max_tokens_is_finite(self):
        """get_wait_time reports a finite but unreachable wait for cost > max_tokens.

        This is a design limitation: the bucket can never hold 1000 tokens, so the
        request can never succeed — but the formula returns a finite number anyway.
        """
        rl = RateLimiter(max_tokens=5, refill_rate=1.0)
        wait = rl.get_wait_time("user1", cost=1000.0, now=100.0)
        # deficit = 995.0, rate = 1.0 → wait = 995.0
        assert wait == pytest.approx(995.0)

    # --- Many requests (collection edge case analog) ---

    def test_handles_100_sequential_requests_correctly(self):
        rl = RateLimiter(max_tokens=100, refill_rate=1.0)
        results = [rl.is_allowed("user1", now=100.0) for _ in range(101)]
        assert results[:100] == [True] * 100
        assert results[100] is False

    # --- Multiple keys at scale ---

    def test_handles_many_independent_keys(self):
        rl = RateLimiter(max_tokens=1, refill_rate=1.0)
        keys = [f"user{i}" for i in range(100)]
        for key in keys:
            assert rl.is_allowed(key, now=100.0) is True
        assert sorted(rl.get_all_keys()) == sorted(keys)

    # --- cleanup_expired at exact boundary ---

    def test_cleanup_expired_keeps_entry_idle_exactly_twice_window(self):
        """Entry idle for exactly 2x window seconds (not strictly greater) is kept."""
        rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("user1", now=100.0)
        # threshold = 120 s; idle exactly 120 s → NOT removed (uses strict >)
        count = rl.cleanup_expired(now=220.0)
        assert count == 0

    # --- get_remaining resets_at after time advances ---

    def test_get_remaining_resets_at_advances_with_refill_time(self):
        rl = RateLimiter(max_tokens=5, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("user1", now=100.0)
        # at now=110, _refill updates last_refill to 110 → resets_at = 170
        status = rl.get_remaining("user1", now=110.0)
        assert status["resets_at"] == pytest.approx(170.0)

    # --- Interplay between get_wait_time and is_allowed ---

    @pytest.mark.skip(reason="BUG: get_wait_time does not call _clean_window, causing stale window data after calls")
    def test_get_wait_time_does_not_call_clean_window_BUG(self):
        """
        BUG: get_wait_time does not call _clean_window, unlike is_allowed and
        get_remaining which both call it.  This means stale timestamps accumulate in
        the sliding window when only get_wait_time is called between is_allowed calls.

        ROOT CAUSE: rate_limiter.py:66-81 — get_wait_time calls _get_or_create and
        _refill but not _clean_window.

        CODE LOCATION: rate_limiter.py:74-81

        CURRENT CODE:
            entry = self._get_or_create(key, now)
            self._refill(entry, now)
            # _clean_window is missing here

        PROPOSED FIX: Add self._clean_window(entry, now) after the _refill call,
        consistent with is_allowed and get_remaining.

        IMPACT: get_wait_time itself does not USE request_timestamps, so the functional
        result of get_wait_time is correct.  However, the inconsistency means that
        a caller checking requests_in_window via get_remaining after a series of
        get_wait_time calls may see stale (too-high) counts.

        EXPECTED: requests_in_window reflects only timestamps within the window
        ACTUAL:   Stale timestamps outside the window remain until cleaned by
                  is_allowed or get_remaining
        """
        rl = RateLimiter(max_tokens=10, refill_rate=1.0, window_seconds=60.0)
        rl.is_allowed("user1", now=100.0)   # ts=100 recorded
        # Only call get_wait_time (does not clean window)
        rl.get_wait_time("user1", now=200.0)  # ts=100 is now 100s old, outside 60s window
        # Without _clean_window in get_wait_time, the stale ts is only cleaned lazily
        # get_remaining DOES call _clean_window, so this test passes trivially —
        # the bug only matters if some internal state is inspected before get_remaining.
        # We document the asymmetry as a code quality / latent bug.
        status = rl.get_remaining("user1", now=200.0)
        assert status["requests_in_window"] == 0
