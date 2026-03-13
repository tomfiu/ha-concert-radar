"""Tests for Concert Radar data models."""

from datetime import date, datetime, timedelta, timezone

from custom_components.concert_radar.models import ConcertEvent


def test_distance_mi(mock_concert_event):
    """Test distance in miles calculation."""
    assert mock_concert_event.distance_mi == 7.7


def test_days_until(mock_concert_event):
    """Test days until calculation."""
    # Create an event 30 days in the future
    future_event = ConcertEvent(
        event_id="test",
        source="ticketmaster",
        artist="Test",
        event_date=datetime.combine(
            date.today() + timedelta(days=30), datetime.min.time()
        ),
        venue_name="Test",
        venue_city="Test",
        venue_country="GB",
        venue_latitude=0,
        venue_longitude=0,
        distance_km=0,
    )
    assert future_event.days_until == 30


def test_days_until_past_event():
    """Test days until returns 0 for past events."""
    past_event = ConcertEvent(
        event_id="test",
        source="ticketmaster",
        artist="Test",
        event_date=datetime(2020, 1, 1),
        venue_name="Test",
        venue_city="Test",
        venue_country="GB",
        venue_latitude=0,
        venue_longitude=0,
        distance_km=0,
    )
    assert past_event.days_until == 0


def test_dedup_key(mock_concert_event):
    """Test dedup key generation."""
    key = mock_concert_event.dedup_key
    assert key == "radiohead|2025-06-15|london"


def test_dedup_key_case_insensitive():
    """Test dedup key is case insensitive."""
    event1 = ConcertEvent(
        event_id="1",
        source="ticketmaster",
        artist="RADIOHEAD",
        event_date=datetime(2025, 6, 15),
        venue_name="Test",
        venue_city="LONDON",
        venue_country="GB",
        venue_latitude=0,
        venue_longitude=0,
        distance_km=0,
    )
    event2 = ConcertEvent(
        event_id="2",
        source="bandsintown",
        artist="radiohead",
        event_date=datetime(2025, 6, 15),
        venue_name="Test",
        venue_city="london",
        venue_country="GB",
        venue_latitude=0,
        venue_longitude=0,
        distance_km=0,
    )
    assert event1.dedup_key == event2.dedup_key
