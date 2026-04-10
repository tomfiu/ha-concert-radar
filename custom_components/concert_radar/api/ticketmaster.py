"""Ticketmaster Discovery API client."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from aiohttp import ClientSession

from ..models import ConcertEvent
from ..utils import haversine
from .base import BaseConcertAPIClient

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://app.ticketmaster.com/discovery/v2"


class TicketmasterClient(BaseConcertAPIClient):
    """Client for the Ticketmaster Discovery API."""

    def __init__(self, api_key: str, session: ClientSession) -> None:
        """Initialize the Ticketmaster client."""
        super().__init__(session)
        self._api_key = api_key

    async def get_events(
        self,
        artist: str,
        lat: float,
        lon: float,
        radius_km: float,
        lookahead_days: int,
    ) -> list[ConcertEvent]:
        """Fetch upcoming events from Ticketmaster."""
        events: list[ConcertEvent] = []
        page = 0
        max_pages = 5

        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=lookahead_days)

        while page < max_pages:
            params = {
                "keyword": artist,
                "classificationName": "music",
                "latlong": f"{lat},{lon}",
                "radius": str(int(radius_km)),
                "unit": "km",
                "startDateTime": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "endDateTime": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "size": "50",
                "page": str(page),
                "apikey": self._api_key,
            }

            resp = await self._get_with_retry(
                f"{BASE_URL}/events.json",
                params=params,
                timeout=30,
                abort_statuses=(401,),
            )
            if resp is None:
                break
            if resp.status == 401:
                _LOGGER.error("Invalid Ticketmaster API key")
                break
            if resp.status != 200:
                break
            try:
                data = await resp.json()
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Failed to parse Ticketmaster response: %s", err)
                break

            embedded = data.get("_embedded")
            if not embedded or "events" not in embedded:
                break

            for raw_event in embedded["events"]:
                event = self._parse_event(raw_event, artist, lat, lon)
                if event:
                    events.append(event)

            # Check pagination
            page_info = data.get("page", {})
            total_pages = page_info.get("totalPages", 1)
            page += 1
            if page >= total_pages:
                break

        return events

    async def validate_api_key(self) -> bool:
        """Test the API key with a simple request."""
        params = {
            "keyword": "test",
            "size": "1",
            "apikey": self._api_key,
        }
        try:
            async with self._session.get(
                f"{BASE_URL}/events.json",
                params=params,
                timeout=15,
            ) as resp:
                return resp.status != 401
        except (ClientError, TimeoutError):
            return False

    def _parse_event(
        self,
        raw: dict,
        artist: str,
        home_lat: float,
        home_lon: float,
    ) -> ConcertEvent | None:
        """Parse a Ticketmaster event into a ConcertEvent."""
        try:
            venues = raw.get("_embedded", {}).get("venues", [])
            if not venues:
                return None

            venue = venues[0]
            location = venue.get("location", {})
            venue_lat = float(location.get("latitude", 0))
            venue_lon = float(location.get("longitude", 0))

            if not venue_lat and not venue_lon:
                return None

            dates = raw.get("dates", {})
            start = dates.get("start", {})
            date_str = start.get("dateTime")
            if not date_str:
                local_date = start.get("localDate")
                local_time = start.get("localTime", "20:00:00")
                if not local_date:
                    return None
                date_str = f"{local_date}T{local_time}"

            if date_str.endswith("Z"):
                event_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                try:
                    event_date = datetime.fromisoformat(date_str)
                except ValueError:
                    return None

            distance = haversine(home_lat, home_lon, venue_lat, venue_lon)

            price_ranges = raw.get("priceRanges", [])
            price_min = None
            price_max = None
            currency = None
            if price_ranges:
                price_min = price_ranges[0].get("min")
                price_max = price_ranges[0].get("max")
                currency = price_ranges[0].get("currency")

            status = dates.get("status", {}).get("code", "")
            on_sale = status == "onsale"

            images = raw.get("images", [])
            image_url = None
            for img in images:
                if img.get("ratio") == "16_9":
                    image_url = img.get("url")
                    break
            if not image_url and images:
                image_url = images[0].get("url")

            return ConcertEvent(
                event_id=raw["id"],
                source="ticketmaster",
                artist=artist,
                event_date=event_date,
                venue_name=venue.get("name", "Unknown Venue"),
                venue_city=venue.get("city", {}).get("name", "Unknown"),
                venue_country=venue.get("country", {}).get("countryCode", ""),
                venue_latitude=venue_lat,
                venue_longitude=venue_lon,
                distance_km=round(distance, 1),
                event_name=raw.get("name"),
                ticket_url=raw.get("url"),
                event_image_url=image_url,
                price_min=price_min,
                price_max=price_max,
                currency=currency,
                on_sale=on_sale,
            )
        except (KeyError, ValueError, TypeError) as err:
            _LOGGER.debug("Failed to parse Ticketmaster event: %s", err)
            return None
