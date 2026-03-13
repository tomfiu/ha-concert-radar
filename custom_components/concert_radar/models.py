"""Data models for the Concert Radar integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class ConcertEvent:
    """Represents a single concert/live event."""

    # Required
    event_id: str
    source: str  # "ticketmaster" | "bandsintown"
    artist: str
    event_date: datetime
    venue_name: str
    venue_city: str
    venue_country: str
    venue_latitude: float
    venue_longitude: float
    distance_km: float

    # Optional
    event_name: Optional[str] = None
    ticket_url: Optional[str] = None
    event_image_url: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    currency: Optional[str] = None
    on_sale: Optional[bool] = None
    lineup: list[str] = field(default_factory=list)

    @property
    def distance_mi(self) -> float:
        """Return distance in miles."""
        return round(self.distance_km * 0.621371, 1)

    @property
    def days_until(self) -> int:
        """Return days until the event."""
        delta = self.event_date.date() - date.today()
        return max(0, delta.days)

    @property
    def dedup_key(self) -> str:
        """Key used to deduplicate events across sources."""
        return f"{self.artist.lower()}|{self.event_date.date()}|{self.venue_city.lower()}"
