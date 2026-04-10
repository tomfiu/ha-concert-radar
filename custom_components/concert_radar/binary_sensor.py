"""Binary sensor platform for Concert Radar."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_ARTIST, ATTR_DAYS_UNTIL, ATTR_EVENT_NAME, ATTR_TICKET_URL, ATTR_VENUE_CITY, ATTR_VENUE_NAME, DOMAIN
from .coordinator import ConcertRadarCoordinator
from .utils import slugify_artist


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Concert Radar binary sensors."""
    coordinator: ConcertRadarCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[BinarySensorEntity] = []

    for artist in coordinator.artists:
        entities.append(
            ConcertRadarHasNearbyConcertBinarySensor(coordinator, artist)
        )
        entities.append(
            ConcertRadarTicketsOnSaleBinarySensor(coordinator, artist)
        )

    entities.append(ConcertRadarAnyNearbyConcertBinarySensor(coordinator))
    entities.append(ConcertRadarApiHealthyBinarySensor(coordinator))

    async_add_entities(entities)


class ConcertRadarBaseBinarySensor(
    CoordinatorEntity[ConcertRadarCoordinator], BinarySensorEntity
):
    """Base class for Concert Radar binary sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ConcertRadarCoordinator) -> None:
        """Initialize the binary sensor."""
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


class ConcertRadarHasNearbyConcertBinarySensor(ConcertRadarBaseBinarySensor):
    """Binary sensor indicating if an artist has a nearby concert."""

    def __init__(
        self, coordinator: ConcertRadarCoordinator, artist: str
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._artist = artist
        slug = slugify_artist(artist)
        self._attr_unique_id = f"{DOMAIN}_{slug}_has_nearby_concert"
        self._attr_name = f"{artist} Has Nearby Concert"

    @property
    def is_on(self) -> bool:
        """Return true if there is a nearby concert."""
        if not self.coordinator.data:
            return False
        return len(self.coordinator.data.get(self._artist, [])) > 0

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:radar" if self.is_on else "mdi:music-off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return sensor attributes."""
        attrs: dict[str, Any] = {ATTR_ARTIST: self._artist}
        if self.coordinator.data:
            events = self.coordinator.data.get(self._artist, [])
            if events:
                next_event = events[0]
                attrs["next_concert_event_name"] = next_event.event_name
                attrs["next_concert_date"] = next_event.event_date.isoformat()
                attrs["next_concert_venue"] = next_event.venue_name
                attrs["next_concert_city"] = next_event.venue_city
                attrs["next_concert_source"] = next_event.source
                attrs[ATTR_DAYS_UNTIL] = next_event.days_until
        return attrs


class ConcertRadarAnyNearbyConcertBinarySensor(ConcertRadarBaseBinarySensor):
    """Binary sensor indicating if any tracked artist has a nearby concert."""

    _attr_icon = "mdi:radar"

    def __init__(self, coordinator: ConcertRadarCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_any_nearby_concert"
        self._attr_name = "Any Nearby Concert"

    @property
    def is_on(self) -> bool:
        """Return true if any artist has a nearby concert."""
        if not self.coordinator.data:
            return False
        return any(
            len(events) > 0 for events in self.coordinator.data.values()
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return sensor attributes."""
        if not self.coordinator.data:
            return {}
        artists_with_concerts = [
            artist
            for artist, events in self.coordinator.data.items()
            if events
        ]
        return {"artists_with_concerts": artists_with_concerts}


class ConcertRadarTicketsOnSaleBinarySensor(ConcertRadarBaseBinarySensor):
    """Binary sensor indicating whether tickets for the next concert are on sale."""

    def __init__(
        self, coordinator: ConcertRadarCoordinator, artist: str
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._artist = artist
        slug = slugify_artist(artist)
        self._attr_unique_id = f"{DOMAIN}_{slug}_tickets_on_sale"
        self._attr_name = f"{artist} Tickets On Sale"

    @property
    def is_on(self) -> bool:
        """Return true if tickets for the next concert are currently on sale."""
        if not self.coordinator.data:
            return False
        events = self.coordinator.data.get(self._artist, [])
        return bool(events and events[0].on_sale)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:ticket-confirmation" if self.is_on else "mdi:ticket-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return sensor attributes."""
        attrs: dict[str, Any] = {ATTR_ARTIST: self._artist}
        if self.coordinator.data:
            events = self.coordinator.data.get(self._artist, [])
            if events:
                event = events[0]
                attrs[ATTR_EVENT_NAME] = event.event_name
                attrs["event_date"] = event.event_date.isoformat()
                attrs[ATTR_VENUE_NAME] = event.venue_name
                attrs[ATTR_VENUE_CITY] = event.venue_city
                attrs[ATTR_TICKET_URL] = event.ticket_url
                attrs[ATTR_DAYS_UNTIL] = event.days_until
        return attrs


class ConcertRadarApiHealthyBinarySensor(ConcertRadarBaseBinarySensor):
    """Binary sensor indicating whether the Concert Radar API connections are healthy."""

    _attr_icon = "mdi:cloud-check-outline"

    def __init__(self, coordinator: ConcertRadarCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_api_healthy"
        self._attr_name = "API Healthy"

    @property
    def is_on(self) -> bool:
        """Return true if the last coordinator update succeeded."""
        return self.coordinator.last_update_success

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:cloud-check-outline" if self.is_on else "mdi:cloud-off-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return sensor attributes."""
        return {
            "last_successful_update": (
                self.coordinator.last_update_success_time.isoformat()
                if self.coordinator.last_update_success_time
                else None
            ),
        }
