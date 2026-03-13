"""Sensor platform for Concert Radar."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ARTIST,
    ATTR_CONCERTS,
    ATTR_CURRENCY,
    ATTR_DAYS_UNTIL,
    ATTR_DISTANCE_KM,
    ATTR_DISTANCE_MI,
    ATTR_EVENT_IMAGE_URL,
    ATTR_EVENT_NAME,
    ATTR_LAST_UPDATED,
    ATTR_ON_SALE,
    ATTR_PRICE_MAX,
    ATTR_PRICE_MIN,
    ATTR_SOURCE,
    ATTR_TICKET_URL,
    ATTR_VENUE_CITY,
    ATTR_VENUE_COUNTRY,
    ATTR_VENUE_LATITUDE,
    ATTR_VENUE_LONGITUDE,
    ATTR_VENUE_NAME,
    DOMAIN,
)
from .coordinator import ConcertRadarCoordinator
from .models import ConcertEvent
from .utils import slugify_artist


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Concert Radar sensors."""
    coordinator: ConcertRadarCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SensorEntity] = []

    for artist in coordinator.artists:
        entities.append(ConcertRadarNextConcertSensor(coordinator, artist))
        entities.append(ConcertRadarUpcomingCountSensor(coordinator, artist))

    entities.append(ConcertRadarTotalUpcomingSensor(coordinator))
    entities.append(ConcertRadarLastUpdatedSensor(coordinator))

    async_add_entities(entities)


class ConcertRadarBaseSensor(CoordinatorEntity[ConcertRadarCoordinator], SensorEntity):
    """Base class for Concert Radar sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ConcertRadarCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "Concert Radar",
            "manufacturer": "Concert Radar",
            "model": "HACS Integration",
            "sw_version": "1.0.0",
        }


class ConcertRadarNextConcertSensor(ConcertRadarBaseSensor):
    """Sensor for the next upcoming concert of an artist."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:ticket-outline"

    def __init__(
        self, coordinator: ConcertRadarCoordinator, artist: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._artist = artist
        slug = slugify_artist(artist)
        self._attr_unique_id = f"{DOMAIN}_{slug}_next_concert"
        self._attr_name = f"{artist} Next Concert"

    @property
    def native_value(self) -> datetime | None:
        """Return the date of the next concert."""
        events = self._get_events()
        if events:
            return events[0].event_date
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return sensor attributes."""
        events = self._get_events()
        if not events:
            return {ATTR_ARTIST: self._artist}

        event = events[0]
        attrs: dict[str, Any] = {
            ATTR_ARTIST: self._artist,
            ATTR_EVENT_NAME: event.event_name,
            ATTR_VENUE_NAME: event.venue_name,
            ATTR_VENUE_CITY: event.venue_city,
            ATTR_VENUE_COUNTRY: event.venue_country,
            ATTR_VENUE_LATITUDE: event.venue_latitude,
            ATTR_VENUE_LONGITUDE: event.venue_longitude,
            ATTR_DISTANCE_KM: event.distance_km,
            ATTR_DISTANCE_MI: event.distance_mi,
            ATTR_TICKET_URL: event.ticket_url,
            ATTR_EVENT_IMAGE_URL: event.event_image_url,
            ATTR_SOURCE: event.source,
            ATTR_DAYS_UNTIL: event.days_until,
            ATTR_ON_SALE: event.on_sale,
        }
        if event.price_min is not None:
            attrs[ATTR_PRICE_MIN] = event.price_min
        if event.price_max is not None:
            attrs[ATTR_PRICE_MAX] = event.price_max
        if event.currency:
            attrs[ATTR_CURRENCY] = event.currency
        return attrs

    def _get_events(self) -> list[ConcertEvent]:
        """Get events for the artist."""
        if not self.coordinator.data:
            return []
        return self.coordinator.data.get(self._artist, [])


class ConcertRadarUpcomingCountSensor(ConcertRadarBaseSensor):
    """Sensor for the number of upcoming concerts of an artist."""

    _attr_icon = "mdi:music-note-plus"
    _attr_native_unit_of_measurement = "concerts"

    def __init__(
        self, coordinator: ConcertRadarCoordinator, artist: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._artist = artist
        slug = slugify_artist(artist)
        self._attr_unique_id = f"{DOMAIN}_{slug}_upcoming_count"
        self._attr_name = f"{artist} Upcoming Concerts"

    @property
    def native_value(self) -> int:
        """Return the number of upcoming concerts."""
        if not self.coordinator.data:
            return 0
        return len(self.coordinator.data.get(self._artist, []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return sensor attributes."""
        events = (
            self.coordinator.data.get(self._artist, [])
            if self.coordinator.data
            else []
        )
        concerts = [
            {
                ATTR_EVENT_NAME: e.event_name,
                "date": e.event_date.isoformat(),
                ATTR_VENUE_NAME: e.venue_name,
                ATTR_VENUE_CITY: e.venue_city,
                ATTR_DISTANCE_KM: e.distance_km,
                ATTR_SOURCE: e.source,
                ATTR_TICKET_URL: e.ticket_url,
            }
            for e in events
        ]
        return {ATTR_ARTIST: self._artist, ATTR_CONCERTS: concerts}


class ConcertRadarTotalUpcomingSensor(ConcertRadarBaseSensor):
    """Sensor for the total number of upcoming concerts across all artists."""

    _attr_icon = "mdi:music-circle"
    _attr_native_unit_of_measurement = "concerts"

    def __init__(self, coordinator: ConcertRadarCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_total_upcoming"
        self._attr_name = "Total Upcoming Concerts"

    @property
    def native_value(self) -> int:
        """Return total upcoming concerts."""
        if not self.coordinator.data:
            return 0
        return sum(len(events) for events in self.coordinator.data.values())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return sensor attributes."""
        if not self.coordinator.data:
            return {}

        artists_with_concerts = []
        for artist, events in self.coordinator.data.items():
            if events:
                artists_with_concerts.append(
                    {
                        ATTR_ARTIST: artist,
                        "count": len(events),
                        "next_date": events[0].event_date.isoformat(),
                    }
                )
        return {
            "artists_with_concerts": artists_with_concerts,
            ATTR_LAST_UPDATED: (
                self.coordinator.last_update_success_time.isoformat()
                if self.coordinator.last_update_success_time
                else None
            ),
        }


class ConcertRadarLastUpdatedSensor(ConcertRadarBaseSensor):
    """Sensor for the last API poll timestamp."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: ConcertRadarCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_last_updated"
        self._attr_name = "Last Updated"

    @property
    def native_value(self) -> datetime | None:
        """Return the last update time."""
        return self.coordinator.last_update_success_time
