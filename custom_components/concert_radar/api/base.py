"""Abstract base class for Concert Radar API clients."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession

from ..models import ConcertEvent

_LOGGER = logging.getLogger(__name__)

_RETRY_DELAYS = (2, 4, 8)  # seconds between retries (3 attempts total)


class BaseConcertAPIClient(ABC):
    """Abstract base class for concert API clients."""

    def __init__(self, session: ClientSession) -> None:
        """Initialize the API client."""
        self._session = session

    @abstractmethod
    async def get_events(
        self,
        artist: str,
        lat: float,
        lon: float,
        radius_km: float,
        lookahead_days: int,
    ) -> list[ConcertEvent]:
        """Fetch upcoming events for the given artist near the given location."""

    async def _get_with_retry(
        self,
        url: str,
        params: dict[str, Any],
        timeout: int = 30,
        abort_statuses: tuple[int, ...] = (401, 403),
    ) -> ClientResponse | None:
        """GET a URL with exponential-backoff retry on transient failures.

        Returns the successful ``ClientResponse`` (caller must read it before
        the context manager exits) or *None* when all attempts fail or a
        permanent error status is encountered.
        """
        last_err: Exception | None = None
        for attempt, delay in enumerate((*_RETRY_DELAYS, None), start=1):
            try:
                resp = await self._session.get(url, params=params, timeout=timeout)
                if resp.status in abort_statuses:
                    # Non-transient error; no point retrying
                    _LOGGER.error(
                        "Permanent HTTP %s from %s — aborting retries", resp.status, url
                    )
                    return resp
                if resp.status == 429:
                    _LOGGER.warning("Rate limited by %s (attempt %d)", url, attempt)
                    # Treat as transient; fall through to retry
                elif resp.status != 200:
                    _LOGGER.warning(
                        "HTTP %s from %s (attempt %d)", resp.status, url, attempt
                    )
                else:
                    return resp
            except (ClientError, TimeoutError, asyncio.TimeoutError) as err:
                last_err = err
                _LOGGER.warning(
                    "Request to %s failed (attempt %d): %s", url, attempt, err
                )

            if delay is not None:
                await asyncio.sleep(delay)

        _LOGGER.error(
            "All retries exhausted for %s. Last error: %s", url, last_err
        )
        return None
