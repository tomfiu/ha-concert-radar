"""Bandsintown API client."""

from __future__ import annotations

import logging
from datetime import datetime

from aiohttp import ClientSession, ClientError

from ..models import ConcertEvent
from ..utils import haversine
from .base import BaseConcertAPIClient

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://rest.bandsintown.com"


class BandsinTownClient(BaseConcertAPIClient):
    """Client for the Bandsintown API."""

    def __init__(self, app_id: str, session: ClientSession) -> None:
        """Initialize the Bandsintown client."""
        super().__init__(session)
        self._app_id = app_id

    async def get_events(
        self,
        artist: str,
        lat: float,
        lon: float,
        radius_km: float,
        lookahead_days: int,
    ) -> list[ConcertEvent]:
        """Fetch upcoming events from Bandsintown with client-side geo-filtering."""
        encoded_artist = artist.replace("/", "%252F")
        url = f"{BASE_URL}/artists/{encoded_artist}/events"

        try:
            async with self._session.get(
                url,
                params={"app_id": self._app_id},
                timeout=30,
            ) as resp:
                if resp.status == 404:
                    _LOGGER.debug("Artist '%s' not found on Bandsintown", artist)
                    return []
                if resp.status != 200:
                    _LOGGER.warning(
                        "Bandsintown API returned status %s for '%s'",
                        resp.status,
                        artist,
                    )
                    return []

                data = await resp.json()
        except (ClientError, TimeoutError) as err:
            _LOGGER.warning("Bandsintown API request failed for '%s': %s", artist, err)
            return []

        if not isinstance(data, list):
            return []

        events: list[ConcertEvent] = []
        for raw_event in data:
            event = self._parse_event(raw_event, artist, lat, lon, radius_km)
            if event:
                events.append(event)

        return events

    def _parse_event(
        self,
        raw: dict,
        artist: str,
        home_lat: float,
        home_lon: float,
        radius_km: float,
    ) -> ConcertEvent | None:
        """Parse a Bandsintown event into a ConcertEvent with geo-filtering."""
        try:
            venue = raw.get("venue", {})
            venue_lat_str = venue.get("latitude")
            venue_lon_str = venue.get("longitude")

            if not venue_lat_str or not venue_lon_str:
                return None

            venue_lat = float(venue_lat_str)
            venue_lon = float(venue_lon_str)

            if venue_lat == 0 and venue_lon == 0:
                return None

            distance = haversine(home_lat, home_lon, venue_lat, venue_lon)

            # Client-side geo-filter
            if distance > radius_km:
                return None

            date_str = raw.get("datetime", "")
            if not date_str:
                return None

            try:
                event_date = datetime.fromisoformat(date_str)
            except ValueError:
                # Try parsing without timezone
                try:
                    event_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    return None

            offers = raw.get("offers", [])
            ticket_url = None
            if offers:
                ticket_url = offers[0].get("url")

            artist_info = raw.get("artist", {})
            image_url = artist_info.get("image_url") if artist_info else None

            lineup = raw.get("lineup", [])

            return ConcertEvent(
                event_id=str(raw.get("id", "")),
                source="bandsintown",
                artist=artist,
                event_date=event_date,
                venue_name=venue.get("name", "Unknown Venue"),
                venue_city=venue.get("city", "Unknown"),
                venue_country=venue.get("country", ""),
                venue_latitude=venue_lat,
                venue_longitude=venue_lon,
                distance_km=round(distance, 1),
                event_name=raw.get("title"),
                ticket_url=ticket_url,
                event_image_url=image_url,
                lineup=lineup,
            )
        except (KeyError, ValueError, TypeError) as err:
            _LOGGER.debug("Failed to parse Bandsintown event: %s", err)
            return None
