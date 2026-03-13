"""Abstract base class for Concert Radar API clients."""

from __future__ import annotations

from abc import ABC, abstractmethod

from aiohttp import ClientSession

from ..models import ConcertEvent


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
