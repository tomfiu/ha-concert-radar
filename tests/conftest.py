"""Fixtures for Concert Radar tests."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from types import ModuleType
from unittest.mock import MagicMock

# Mock homeassistant and its submodules before importing our code
_HA_MODULES = [
    "homeassistant",
    "homeassistant.config_entries",
    "homeassistant.core",
    "homeassistant.helpers",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.helpers.entity_platform",
    "homeassistant.components",
    "homeassistant.components.sensor",
    "homeassistant.components.binary_sensor",
    "homeassistant.components.calendar",
    "homeassistant.data_entry_flow",
]

for mod_name in _HA_MODULES:
    if mod_name not in sys.modules:
        mock_mod = MagicMock()
        sys.modules[mod_name] = mock_mod

# Set up specific HA mock attributes needed by our code
ha_sensor = sys.modules["homeassistant.components.sensor"]
ha_sensor.SensorDeviceClass = MagicMock()
ha_sensor.SensorDeviceClass.TIMESTAMP = "timestamp"
ha_sensor.SensorEntity = type("SensorEntity", (), {})

ha_binary = sys.modules["homeassistant.components.binary_sensor"]
ha_binary.BinarySensorEntity = type("BinarySensorEntity", (), {})

ha_calendar = sys.modules["homeassistant.components.calendar"]
ha_calendar.CalendarEntity = type("CalendarEntity", (), {})
ha_calendar.CalendarEvent = MagicMock()

ha_coordinator = sys.modules["homeassistant.helpers.update_coordinator"]
ha_coordinator.CoordinatorEntity = type("CoordinatorEntity", (object,), {"__init_subclass__": lambda **kw: None})


class _SubscriptableType(type):
    def __getitem__(cls, item):
        return cls


ha_coordinator.DataUpdateCoordinator = _SubscriptableType("DataUpdateCoordinator", (), {})
ha_coordinator.UpdateFailed = Exception

ha_config = sys.modules["homeassistant.config_entries"]
ha_config.ConfigEntry = MagicMock()
ha_config.ConfigFlow = type("ConfigFlow", (), {})
ha_config.OptionsFlow = type("OptionsFlow", (), {})

ha_flow = sys.modules["homeassistant.data_entry_flow"]
ha_flow.FlowResult = dict

import pytest

from custom_components.concert_radar.models import ConcertEvent


MOCK_TM_RESPONSE = {
    "_embedded": {
        "events": [
            {
                "id": "tm_001",
                "name": "Radiohead Live 2025",
                "dates": {
                    "start": {"dateTime": "2025-06-15T19:00:00Z"},
                    "status": {"code": "onsale"},
                },
                "_embedded": {
                    "venues": [
                        {
                            "name": "O2 Arena",
                            "city": {"name": "London"},
                            "country": {"countryCode": "GB"},
                            "location": {
                                "latitude": "51.5033",
                                "longitude": "0.0030",
                            },
                        }
                    ]
                },
                "url": "https://ticketmaster.com/event/001",
                "images": [
                    {"ratio": "16_9", "url": "https://example.com/image.jpg"}
                ],
                "priceRanges": [
                    {"min": 45.0, "max": 120.0, "currency": "GBP"}
                ],
            }
        ]
    },
    "page": {"totalPages": 1, "totalElements": 1},
}

MOCK_TM_EMPTY_RESPONSE = {
    "page": {"totalPages": 0, "totalElements": 0},
}

MOCK_BIT_RESPONSE = [
    {
        "id": "bit_001",
        "datetime": "2025-07-04T20:00:00",
        "title": "Massive Attack Festival",
        "venue": {
            "name": "Brixton Academy",
            "city": "London",
            "country": "United Kingdom",
            "latitude": "51.4613",
            "longitude": "-0.1156",
        },
        "offers": [{"url": "https://bandsintown.com/e/bit_001"}],
        "artist": {"name": "Massive Attack", "image_url": "https://example.com/ma.jpg"},
        "lineup": ["Massive Attack", "Support Act"],
    }
]


@pytest.fixture
def mock_concert_event() -> ConcertEvent:
    """Return a mock ConcertEvent."""
    return ConcertEvent(
        event_id="tm_001",
        source="ticketmaster",
        artist="Radiohead",
        event_date=datetime(2025, 6, 15, 19, 0, 0, tzinfo=timezone.utc),
        venue_name="O2 Arena",
        venue_city="London",
        venue_country="GB",
        venue_latitude=51.5033,
        venue_longitude=0.0030,
        distance_km=12.4,
        event_name="Radiohead Live 2025",
        ticket_url="https://ticketmaster.com/event/001",
        event_image_url="https://example.com/image.jpg",
        price_min=45.0,
        price_max=120.0,
        currency="GBP",
        on_sale=True,
    )


@pytest.fixture
def mock_concert_event_bandsintown() -> ConcertEvent:
    """Return a mock ConcertEvent from Bandsintown."""
    return ConcertEvent(
        event_id="bit_001",
        source="bandsintown",
        artist="Massive Attack",
        event_date=datetime(2025, 7, 4, 20, 0, 0),
        venue_name="Brixton Academy",
        venue_city="London",
        venue_country="United Kingdom",
        venue_latitude=51.4613,
        venue_longitude=-0.1156,
        distance_km=8.2,
        event_name="Massive Attack Festival",
        ticket_url="https://bandsintown.com/e/bit_001",
        lineup=["Massive Attack", "Support Act"],
    )
