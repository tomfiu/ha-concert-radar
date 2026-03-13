"""Utility functions for the Concert Radar integration."""

from __future__ import annotations

import math
import re

from .models import ConcertEvent


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in km between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def slugify_artist(name: str) -> str:
    """Convert artist name to a safe entity ID component."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def deduplicate_events(events: list[ConcertEvent]) -> list[ConcertEvent]:
    """Remove duplicate events across sources. Ticketmaster takes priority."""
    seen: dict[str, ConcertEvent] = {}
    for event in sorted(events, key=lambda e: 0 if e.source == "ticketmaster" else 1):
        key = event.dedup_key
        if key not in seen:
            seen[key] = event
    return sorted(seen.values(), key=lambda e: e.event_date)


def km_to_miles(km: float) -> float:
    """Convert kilometers to miles."""
    return round(km * 0.621371, 1)
