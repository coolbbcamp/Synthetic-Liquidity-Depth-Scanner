from __future__ import annotations

from types import TracebackType

import httpx

from liquidity_scanner.config import Settings
from liquidity_scanner.probe.jupiter import JupiterClient
from liquidity_scanner.probe.rate_limit import TokenBucketRateLimiter


class JupiterProbeSession:
    """Shared HTTP client + rate limiter for sequential free-tier probing."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.limiter = TokenBucketRateLimiter(settings.jup_rps)
        self._client: httpx.AsyncClient | None = None
        self.credits_used = 0

    async def __aenter__(self) -> JupiterProbeSession:
        self._client = httpx.AsyncClient()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def jupiter(self) -> JupiterClient:
        if self._client is None:
            raise RuntimeError("JupiterProbeSession is not active")
        client = JupiterClient(self.settings, self._client, self.limiter)
        return client
