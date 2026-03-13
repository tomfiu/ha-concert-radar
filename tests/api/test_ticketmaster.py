"""Tests for the Ticketmaster API client."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.concert_radar.api.ticketmaster import TicketmasterClient
from tests.conftest import MOCK_TM_EMPTY_RESPONSE, MOCK_TM_RESPONSE


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = MagicMock()
    return session


def _mock_response(status=200, data=None):
    """Create a mock response context manager."""
    response = AsyncMock()
    response.status = status
    response.json = AsyncMock(return_value=data or {})

    context = AsyncMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


@pytest.mark.asyncio
async def test_get_events_success(mock_session):
    """Test successful event fetching."""
    mock_session.get = MagicMock(return_value=_mock_response(200, MOCK_TM_RESPONSE))
    client = TicketmasterClient(api_key="test_key", session=mock_session)

    events = await client.get_events("Radiohead", 51.5, -0.1, 150, 180)

    assert len(events) == 1
    event = events[0]
    assert event.artist == "Radiohead"
    assert event.source == "ticketmaster"
    assert event.venue_name == "O2 Arena"
    assert event.venue_city == "London"
    assert event.price_min == 45.0
    assert event.on_sale is True


@pytest.mark.asyncio
async def test_get_events_empty(mock_session):
    """Test empty response."""
    mock_session.get = MagicMock(
        return_value=_mock_response(200, MOCK_TM_EMPTY_RESPONSE)
    )
    client = TicketmasterClient(api_key="test_key", session=mock_session)

    events = await client.get_events("Unknown Artist", 51.5, -0.1, 150, 180)
    assert len(events) == 0


@pytest.mark.asyncio
async def test_get_events_rate_limit(mock_session):
    """Test rate limit handling."""
    mock_session.get = MagicMock(return_value=_mock_response(429))
    client = TicketmasterClient(api_key="test_key", session=mock_session)

    events = await client.get_events("Radiohead", 51.5, -0.1, 150, 180)
    assert len(events) == 0


@pytest.mark.asyncio
async def test_get_events_unauthorized(mock_session):
    """Test invalid API key handling."""
    mock_session.get = MagicMock(return_value=_mock_response(401))
    client = TicketmasterClient(api_key="invalid_key", session=mock_session)

    events = await client.get_events("Radiohead", 51.5, -0.1, 150, 180)
    assert len(events) == 0


@pytest.mark.asyncio
async def test_validate_api_key_success(mock_session):
    """Test API key validation success."""
    mock_session.get = MagicMock(return_value=_mock_response(200, {}))
    client = TicketmasterClient(api_key="valid_key", session=mock_session)

    result = await client.validate_api_key()
    assert result is True


@pytest.mark.asyncio
async def test_validate_api_key_failure(mock_session):
    """Test API key validation failure."""
    mock_session.get = MagicMock(return_value=_mock_response(401))
    client = TicketmasterClient(api_key="invalid_key", session=mock_session)

    result = await client.validate_api_key()
    assert result is False
