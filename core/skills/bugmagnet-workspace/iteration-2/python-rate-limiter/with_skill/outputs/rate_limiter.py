"""Sliding window rate limiter with per-key token bucket tracking."""

import time
from dataclasses import dataclass, field


@dataclass
class _Entry:
    tokens: float
    last_refill: float
    request_timestamps: list[float] = field(default_factory=list)


class RateLimiter:
    """Token bucket rate limiter with sliding window request counting.

    Each key gets an independent token bucket that refills at a fixed rate.
    Requests consume tokens; when no tokens remain, requests are denied.
    A sliding window tracks recent request timestamps for monitoring.
    """

    def __init__(
        self, max_tokens: int, refill_rate: float, window_seconds: float = 60.0
    ):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.window_seconds = window_seconds
        self._entries: dict[str, _Entry] = {}

    def _get_or_create(self, key: str, now: float) -> _Entry:
        if key not in self._entries:
            self._entries[key] = _Entry(
                tokens=float(self.max_tokens), last_refill=now
            )
        return self._entries[key]

    def _refill(self, entry: _Entry, now: float) -> None:
        elapsed = now - entry.last_refill
        if elapsed <= 0:
            return
        added = elapsed * self.refill_rate
        entry.tokens = min(float(self.max_tokens), entry.tokens + added)
        entry.last_refill = now

    def _clean_window(self, entry: _Entry, now: float) -> None:
        cutoff = now - self.window_seconds
        entry.request_timestamps = [
            ts for ts in entry.request_timestamps if ts > cutoff
        ]

    def is_allowed(
        self, key: str, cost: float = 1.0, now: float | None = None
    ) -> bool:
        """Check if a request is allowed and consume tokens if so."""
        now = now if now is not None else time.time()
        entry = self._get_or_create(key, now)
        self._refill(entry, now)
        self._clean_window(entry, now)

        if entry.tokens >= cost:
            entry.tokens -= cost
            entry.request_timestamps.append(now)
            return True
        return False

    def get_wait_time(
        self, key: str, cost: float = 1.0, now: float | None = None
    ) -> float:
        """Return seconds until a request with the given cost would be allowed.

        Returns 0.0 if the request would be allowed immediately.
        """
        now = now if now is not None else time.time()
        entry = self._get_or_create(key, now)
        self._refill(entry, now)

        if entry.tokens >= cost:
            return 0.0

        deficit = cost - entry.tokens
        return deficit / self.refill_rate

    def get_remaining(
        self, key: str, now: float | None = None
    ) -> dict:
        """Return current status for a key."""
        now = now if now is not None else time.time()
        entry = self._get_or_create(key, now)
        self._refill(entry, now)
        self._clean_window(entry, now)

        return {
            "remaining_tokens": entry.tokens,
            "requests_in_window": len(entry.request_timestamps),
            "window_seconds": self.window_seconds,
            "resets_at": entry.last_refill + self.window_seconds,
        }

    def cleanup_expired(self, now: float | None = None) -> int:
        """Remove entries idle for longer than twice the window.

        Returns the number of entries removed.
        """
        now = now if now is not None else time.time()
        threshold = self.window_seconds * 2

        expired = [
            key
            for key, entry in self._entries.items()
            if now - entry.last_refill > threshold
        ]
        for key in expired:
            del self._entries[key]
        return len(expired)

    def get_all_keys(self) -> list[str]:
        """Return all currently tracked keys."""
        return list(self._entries.keys())


def create_rate_limiter(requests_per_minute: int) -> RateLimiter:
    """Convenience factory for a requests-per-minute limiter."""
    return RateLimiter(
        max_tokens=requests_per_minute,
        refill_rate=requests_per_minute / 60.0,
        window_seconds=60.0,
    )


def create_burst_limiter(
    burst_size: int, sustained_per_second: float
) -> RateLimiter:
    """Create a limiter allowing bursts but limiting sustained rate."""
    return RateLimiter(
        max_tokens=burst_size,
        refill_rate=sustained_per_second,
        window_seconds=1.0,
    )
