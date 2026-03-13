"""Calendar platform for Concert Radar."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ConcertRadarCoordinator
from .models import ConcertEvent


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Concert Radar calendar."""
    coordinator: ConcertRadarCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([ConcertRadarCalendarEntity(coordinator)])


class ConcertRadarCalendarEntity(
    CoordinatorEntity[ConcertRadarCoordinator], CalendarEntity
):
    """Calendar entity for Concert Radar."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-music"

    def __init__(self, coordinator: ConcertRadarCoordinator) -> None:
        """Initialize the calendar entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_calendar"
        self._attr_name = "Concert Radar"

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

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        all_events = self._get_all_events()
        if not all_events:
            return None

        now = datetime.now()
        future_events = [e for e in all_events if e.event_date > now]
        if not future_events:
            return None

        next_event = future_events[0]
        return self._to_calendar_event(next_event)

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within the date range."""
        all_events = self._get_all_events()
        return [
            self._to_calendar_event(e)
            for e in all_events
            if start_date <= e.event_date <= end_date
        ]

    def _get_all_events(self) -> list[ConcertEvent]:
        """Get all events sorted by date."""
        if not self.coordinator.data:
            return []

        all_events: list[ConcertEvent] = []
        for events in self.coordinator.data.values():
            all_events.extend(events)

        return sorted(all_events, key=lambda e: e.event_date)

    def _to_calendar_event(self, event: ConcertEvent) -> CalendarEvent:
        """Convert a ConcertEvent to a CalendarEvent."""
        description_parts = [
            f"{event.venue_city}, {event.venue_country} — {event.distance_km} km away",
        ]
        if event.ticket_url:
            description_parts.append(f"Tickets: {event.ticket_url}")
        if event.price_min is not None and event.currency:
            description_parts.append(f"From {event.currency} {event.price_min}")

        return CalendarEvent(
            summary=f"{event.artist} @ {event.venue_name}",
            start=event.event_date,
            end=event.event_date + timedelta(hours=3),
            description="\n".join(description_parts),
            location=f"{event.venue_name}, {event.venue_city}, {event.venue_country}",
        )
