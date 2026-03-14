"""Tests for Concert Radar sensor entities."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from custom_components.concert_radar.models import ConcertEvent
from custom_components.concert_radar.sensor import (
    ConcertRadarDistanceSensor,
    ConcertRadarVenueCitySensor,
)


def _make_event(city="London", country="United Kingdom", distance_km=12.4) -> ConcertEvent:
    return ConcertEvent(
        event_id="test_001",
        source="ticketmaster",
        artist="Radiohead",
        event_date=datetime(2025, 6, 15, 19, 0, 0, tzinfo=timezone.utc),
        venue_name="O2 Arena",
        venue_city=city,
        venue_country=country,
        venue_latitude=51.5033,
        venue_longitude=0.0030,
        distance_km=distance_km,
    )


def _make_coordinator(events=None, radius_unit="km") -> MagicMock:
    coordinator = MagicMock()
    coordinator.data = {"Radiohead": events if events is not None else [_make_event()]}
    coordinator.artists = ["Radiohead"]
    # Simulate options not set, data returns the unit
    coordinator.config_entry.options.get.side_effect = lambda key, default=None: default
    coordinator.config_entry.data.get.side_effect = lambda key, default=None: (
        radius_unit if key == "radius_unit" else default
    )
    return coordinator


# ---------------------------------------------------------------------------
# ConcertRadarVenueCitySensor
# ---------------------------------------------------------------------------

class TestVenueCitySensor:
    def test_shows_city_and_country(self):
        coordinator = _make_coordinator(events=[_make_event(city="London", country="United Kingdom")])
        sensor = ConcertRadarVenueCitySensor(coordinator, "Radiohead")
        assert sensor.native_value == "London, United Kingdom"

    def test_shows_country_code(self):
        coordinator = _make_coordinator(events=[_make_event(city="Berlin", country="DE")])
        sensor = ConcertRadarVenueCitySensor(coordinator, "Radiohead")
        assert sensor.native_value == "Berlin, DE"

    def test_falls_back_to_city_when_no_country(self):
        event = _make_event(city="Amsterdam", country="")
        coordinator = _make_coordinator(events=[event])
        sensor = ConcertRadarVenueCitySensor(coordinator, "Radiohead")
        assert sensor.native_value == "Amsterdam"

    def test_returns_none_when_no_events(self):
        coordinator = _make_coordinator(events=[])
        sensor = ConcertRadarVenueCitySensor(coordinator, "Radiohead")
        assert sensor.native_value is None

    def test_returns_none_when_no_data(self):
        coordinator = _make_coordinator()
        coordinator.data = None
        sensor = ConcertRadarVenueCitySensor(coordinator, "Radiohead")
        assert sensor.native_value is None

    def test_attributes_include_country(self):
        coordinator = _make_coordinator(events=[_make_event(country="United Kingdom", distance_km=12.4)])
        sensor = ConcertRadarVenueCitySensor(coordinator, "Radiohead")
        attrs = sensor.extra_state_attributes
        assert attrs["venue_country"] == "United Kingdom"
        assert attrs["distance_km"] == 12.4
        assert "distance_mi" in attrs


# ---------------------------------------------------------------------------
# ConcertRadarDistanceSensor
# ---------------------------------------------------------------------------

class TestDistanceSensor:
    def test_returns_km_by_default(self):
        coordinator = _make_coordinator(events=[_make_event(distance_km=50.0)], radius_unit="km")
        sensor = ConcertRadarDistanceSensor(coordinator, "Radiohead")
        assert sensor.native_value == 50.0
        assert sensor.native_unit_of_measurement == "km"

    def test_returns_miles_when_configured(self):
        coordinator = _make_coordinator(events=[_make_event(distance_km=100.0)], radius_unit="mi")
        # Override so options returns "mi" for radius_unit
        coordinator.config_entry.options.get.side_effect = lambda key, default=None: (
            "mi" if key == "radius_unit" else default
        )
        sensor = ConcertRadarDistanceSensor(coordinator, "Radiohead")
        assert sensor.native_unit_of_measurement == "mi"
        assert sensor.native_value == round(100.0 * 0.621371, 1)

    def test_unit_from_data_when_options_not_set(self):
        coordinator = _make_coordinator(events=[_make_event(distance_km=20.0)], radius_unit="km")
        sensor = ConcertRadarDistanceSensor(coordinator, "Radiohead")
        assert sensor.native_unit_of_measurement == "km"

    def test_returns_none_when_no_events(self):
        coordinator = _make_coordinator(events=[])
        sensor = ConcertRadarDistanceSensor(coordinator, "Radiohead")
        assert sensor.native_value is None

    def test_returns_none_when_no_data(self):
        coordinator = _make_coordinator()
        coordinator.data = None
        sensor = ConcertRadarDistanceSensor(coordinator, "Radiohead")
        assert sensor.native_value is None

    def test_attributes_include_both_units(self):
        coordinator = _make_coordinator(events=[_make_event(distance_km=100.0)])
        sensor = ConcertRadarDistanceSensor(coordinator, "Radiohead")
        attrs = sensor.extra_state_attributes
        assert attrs["distance_km"] == 100.0
        assert "distance_mi" in attrs
        assert attrs["unit"] == "km"

    def test_attributes_include_venue_info(self):
        coordinator = _make_coordinator(
            events=[_make_event(city="Paris", country="France", distance_km=300.0)]
        )
        sensor = ConcertRadarDistanceSensor(coordinator, "Radiohead")
        attrs = sensor.extra_state_attributes
        assert attrs["venue_city"] == "Paris"
        assert attrs["venue_country"] == "France"
        assert attrs["venue_name"] == "O2 Arena"

    def test_value_rounded_to_one_decimal(self):
        coordinator = _make_coordinator(events=[_make_event(distance_km=123.456)])
        sensor = ConcertRadarDistanceSensor(coordinator, "Radiohead")
        assert sensor.native_value == 123.5

    def test_empty_attributes_when_no_events(self):
        coordinator = _make_coordinator(events=[])
        sensor = ConcertRadarDistanceSensor(coordinator, "Radiohead")
        attrs = sensor.extra_state_attributes
        assert attrs == {"artist": "Radiohead"}
