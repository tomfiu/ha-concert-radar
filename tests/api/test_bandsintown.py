"""Tests for the Bandsintown API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.concert_radar.api.bandsintown import BandsinTownClient
from tests.conftest import MOCK_BIT_RESPONSE


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = MagicMock()
    return session


def _mock_response(status=200, data=None):
    """Create a mock response context manager."""
    response = AsyncMock()
    response.status = status
    response.json = AsyncMock(return_value=data or [])

    context = AsyncMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


@pytest.mark.asyncio
async def test_get_events_success(mock_session):
    """Test successful event fetching."""
    mock_session.get = MagicMock(
        return_value=_mock_response(200, MOCK_BIT_RESPONSE)
    )
    client = BandsinTownClient(app_id="test_app", session=mock_session)

    # Use coordinates close to London so the event is within radius
    events = await client.get_events("Massive Attack", 51.5, -0.1, 150, 180)

    assert len(events) == 1
    event = events[0]
    assert event.artist == "Massive Attack"
    assert event.source == "bandsintown"
    assert event.venue_name == "Brixton Academy"
    assert event.venue_city == "London"


@pytest.mark.asyncio
async def test_get_events_geo_filtered(mock_session):
    """Test events outside radius are filtered out."""
    mock_session.get = MagicMock(
        return_value=_mock_response(200, MOCK_BIT_RESPONSE)
    )
    client = BandsinTownClient(app_id="test_app", session=mock_session)

    # Use coordinates far from London (New York)
    events = await client.get_events("Massive Attack", 40.7, -74.0, 50, 180)

    assert len(events) == 0


@pytest.mark.asyncio
async def test_get_events_artist_not_found(mock_session):
    """Test artist not found handling."""
    mock_session.get = MagicMock(return_value=_mock_response(404))
    client = BandsinTownClient(app_id="test_app", session=mock_session)

    events = await client.get_events("Unknown Artist", 51.5, -0.1, 150, 180)
    assert len(events) == 0


@pytest.mark.asyncio
async def test_get_events_empty_response(mock_session):
    """Test empty response handling."""
    mock_session.get = MagicMock(return_value=_mock_response(200, []))
    client = BandsinTownClient(app_id="test_app", session=mock_session)

    events = await client.get_events("Radiohead", 51.5, -0.1, 150, 180)
    assert len(events) == 0
