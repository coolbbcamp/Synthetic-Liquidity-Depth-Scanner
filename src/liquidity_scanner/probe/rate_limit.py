from __future__ import annotations

import asyncio
import time


class TokenBucketRateLimiter:
    """Simple token-bucket limiter with Retry-After support."""

    def __init__(self, rate_per_second: float) -> None:
        self.rate = max(rate_per_second, 0.1)
        self.tokens = self.rate
        self.updated_at = time.monotonic()
        self.retry_until = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                if now < self.retry_until:
                    wait = self.retry_until - now
                else:
                    elapsed = now - self.updated_at
                    self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
                    self.updated_at = now
                    if self.tokens >= 1.0:
                        self.tokens -= 1.0
                        return
                    wait = (1.0 - self.tokens) / self.rate
            await asyncio.sleep(wait)

    def penalize(self, retry_after_seconds: float) -> None:
        self.retry_until = max(self.retry_until, time.monotonic() + retry_after_seconds)
