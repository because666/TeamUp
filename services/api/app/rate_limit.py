from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from time import monotonic


@dataclass(frozen=True)
class RateLimitRule:
    window_seconds: int
    max_requests: int

    def __post_init__(self) -> None:
        if self.window_seconds <= 0 or self.max_requests <= 0:
            raise ValueError("rate limit window and maximum must be positive")


class InMemoryRateLimiter:
    """Thread-safe fixed-window limiter for a single API process."""

    def __init__(self, rules: dict[str, RateLimitRule] | None = None) -> None:
        self.rules = rules or {
            "auth.login": RateLimitRule(60, 60),
            "safety.report": RateLimitRule(60, 30),
            "team.invitation": RateLimitRule(60, 30),
            "messages.send": RateLimitRule(60, 60),
        }
        self._windows: dict[tuple[str, str], tuple[float, int]] = {}
        self._lock = RLock()

    def check(self, scope: str, key: str, now: float | None = None) -> int | None:
        rule = self.rules.get(scope)
        if rule is None:
            return None
        current = monotonic() if now is None else now
        window_start = current - (current % rule.window_seconds)
        compound_key = (scope, key)
        with self._lock:
            self._prune(current)
            stored_start, count = self._windows.get(compound_key, (window_start, 0))
            if stored_start != window_start:
                stored_start, count = window_start, 0
            if count >= rule.max_requests:
                retry_after = max(1, int(stored_start + rule.window_seconds - current))
                self._windows[compound_key] = (stored_start, count)
                return retry_after
            self._windows[compound_key] = (stored_start, count + 1)
            return None

    def clear(self) -> None:
        with self._lock:
            self._windows.clear()

    def _prune(self, now: float) -> None:
        expired = [
            compound_key
            for compound_key, (window_start, _count) in self._windows.items()
            if now >= window_start + self.rules[compound_key[0]].window_seconds
        ]
        for compound_key in expired:
            self._windows.pop(compound_key, None)
