"""DataUpdateCoordinator for Concert Radar."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api.bandsintown import BandsinTownClient
from .api.ticketmaster import TicketmasterClient
from .const import (
    CONF_ARTISTS,
    CONF_BAND_IGNORE_LIST,
    CONF_BIT_APP_ID,
    CONF_IGNORE_TRIBUTE_BANDS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_LOOKAHEAD_DAYS,
    CONF_NOTIFICATIONS,
    CONF_POLL_INTERVAL,
    CONF_RADIUS,
    CONF_TM_API_KEY,
    CONF_USE_HA_LOCATION,
    DEFAULT_BAND_IGNORE_LIST,
    DEFAULT_BANDSINTOWN_APP_ID,
    DEFAULT_IGNORE_TRIBUTE_BANDS,
    DEFAULT_LOOKAHEAD_DAYS,
    DEFAULT_POLL_INTERVAL_HOURS,
    DEFAULT_RADIUS_KM,
    DOMAIN,
    EVENT_ARTIST_ON_TOUR,
    EVENT_NEW_CONCERT,
)
from .models import ConcertEvent
from .utils import deduplicate_events, is_in_ignore_list, is_tribute_or_revival

_LOGGER = logging.getLogger(__name__)


class ConcertRadarCoordinator(DataUpdateCoordinator[dict[str, list[ConcertEvent]]]):
    """Coordinator that polls Ticketmaster and Bandsintown APIs."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.config_entry = config_entry
        self._config = {**config_entry.data, **config_entry.options}
        session = async_get_clientsession(hass)

        self._tm_client = TicketmasterClient(
            api_key=self._config[CONF_TM_API_KEY],
            session=session,
        )
        self._bit_client = BandsinTownClient(
            app_id=self._config.get(CONF_BIT_APP_ID, DEFAULT_BANDSINTOWN_APP_ID),
            session=session,
        )
        self._previous_event_keys: set[str] = set()
        self._previous_artist_states: dict[str, bool] = {}

        poll_interval = self._config.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL_HOURS)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=poll_interval),
        )

    def update_config(self) -> None:
        """Update internal config from config entry."""
        self._config = {**self.config_entry.data, **self.config_entry.options}
        session = async_get_clientsession(self.hass)
        self._tm_client = TicketmasterClient(
            api_key=self._config[CONF_TM_API_KEY],
            session=session,
        )
        self._bit_client = BandsinTownClient(
            app_id=self._config.get(CONF_BIT_APP_ID, DEFAULT_BANDSINTOWN_APP_ID),
            session=session,
        )
        poll_interval = self._config.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL_HOURS)
        self.update_interval = timedelta(hours=poll_interval)

    @property
    def artists(self) -> list[str]:
        """Return list of tracked artists."""
        return self._config.get(CONF_ARTISTS, [])

    async def _async_update_data(self) -> dict[str, list[ConcertEvent]]:
        """Fetch data from both APIs for all artists."""
        artists = self.artists
        lat = self._get_latitude()
        lon = self._get_longitude()
        radius_km = self._config.get(CONF_RADIUS, DEFAULT_RADIUS_KM)
        lookahead = self._config.get(CONF_LOOKAHEAD_DAYS, DEFAULT_LOOKAHEAD_DAYS)

        results: dict[str, list[ConcertEvent]] = {}

        ignore_tributes = self._config.get(
            CONF_IGNORE_TRIBUTE_BANDS, DEFAULT_IGNORE_TRIBUTE_BANDS
        )
        band_ignore_list = self._config.get(CONF_BAND_IGNORE_LIST, DEFAULT_BAND_IGNORE_LIST)

        async def fetch_artist(artist: str) -> tuple[str, list[ConcertEvent]]:
            tm_result, bit_result = await asyncio.gather(
                self._tm_client.get_events(artist, lat, lon, radius_km, lookahead),
                self._bit_client.get_events(artist, lat, lon, radius_km, lookahead),
                return_exceptions=True,
            )
            events: list[ConcertEvent] = []
            if isinstance(tm_result, list):
                events.extend(tm_result)
            elif isinstance(tm_result, Exception):
                _LOGGER.warning(
                    "Ticketmaster fetch failed for '%s': %s", artist, tm_result
                )
            if isinstance(bit_result, list):
                events.extend(bit_result)
            elif isinstance(bit_result, Exception):
                _LOGGER.warning(
                    "Bandsintown fetch failed for '%s': %s", artist, bit_result
                )
            deduped = deduplicate_events(events)
            if ignore_tributes:
                filtered = [e for e in deduped if not is_tribute_or_revival(e)]
                if len(filtered) < len(deduped):
                    _LOGGER.debug(
                        "Filtered %d tribute/revival event(s) for '%s'",
                        len(deduped) - len(filtered),
                        artist,
                    )
                deduped = filtered
            if band_ignore_list:
                filtered = [e for e in deduped if not is_in_ignore_list(e, band_ignore_list)]
                if len(filtered) < len(deduped):
                    _LOGGER.debug(
                        "Filtered %d ignored band event(s) for '%s'",
                        len(deduped) - len(filtered),
                        artist,
                    )
                deduped = filtered
            return artist, deduped

        fetch_tasks = [fetch_artist(a) for a in artists]
        try:
            artist_results = await asyncio.gather(*fetch_tasks)
        except Exception as err:
            raise UpdateFailed(f"Concert Radar update failed: {err}") from err

        all_new_events: list[ConcertEvent] = []
        for artist, events in artist_results:
            results[artist] = events
            for event in events:
                if event.dedup_key not in self._previous_event_keys:
                    all_new_events.append(event)

        # Fire events for new concerts (skip on first poll)
        if self._previous_event_keys:
            for event in all_new_events:
                self.hass.bus.async_fire(
                    EVENT_NEW_CONCERT,
                    {
                        "artist": event.artist,
                        "event_name": event.event_name,
                        "event_date": event.event_date.isoformat(),
                        "venue_name": event.venue_name,
                        "venue_city": event.venue_city,
                        "venue_country": event.venue_country,
                        "distance_km": event.distance_km,
                        "distance_mi": event.distance_mi,
                        "ticket_url": event.ticket_url,
                        "source": event.source,
                    },
                )

            # Fire artist_on_tour events
            for artist, events in results.items():
                had_concerts = self._previous_artist_states.get(artist, False)
                has_concerts = len(events) > 0
                if has_concerts and not had_concerts:
                    self.hass.bus.async_fire(
                        EVENT_ARTIST_ON_TOUR,
                        {
                            "artist": artist,
                            "concert_count": len(events),
                            "next_concert_date": events[0].event_date.isoformat(),
                        },
                    )

            # Create persistent notifications if enabled
            if self._config.get(CONF_NOTIFICATIONS, True) and all_new_events:
                for event in all_new_events:
                    self.hass.components.persistent_notification.async_create(
                        title=f"Concert Alert: {event.artist}",
                        message=(
                            f"{event.artist} is playing at {event.venue_name}, "
                            f"{event.venue_city} on "
                            f"{event.event_date.strftime('%B %d, %Y')} "
                            f"({event.distance_km} km away). "
                            f"[Get Tickets]({event.ticket_url})"
                            if event.ticket_url
                            else f"{event.artist} is playing at {event.venue_name}, "
                            f"{event.venue_city} on "
                            f"{event.event_date.strftime('%B %d, %Y')} "
                            f"({event.distance_km} km away)."
                        ),
                        notification_id=f"concert_radar_{event.dedup_key}",
                    )

        # Update previous state
        self._previous_event_keys = {
            e.dedup_key for events in results.values() for e in events
        }
        self._previous_artist_states = {
            artist: len(events) > 0 for artist, events in results.items()
        }

        return results

    def _get_latitude(self) -> float:
        """Get the latitude to use for searches."""
        if self._config.get(CONF_USE_HA_LOCATION, True):
            return self.hass.config.latitude
        return self._config.get(CONF_LATITUDE, self.hass.config.latitude)

    def _get_longitude(self) -> float:
        """Get the longitude to use for searches."""
        if self._config.get(CONF_USE_HA_LOCATION, True):
            return self.hass.config.longitude
        return self._config.get(CONF_LONGITUDE, self.hass.config.longitude)
