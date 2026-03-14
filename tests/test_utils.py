"""Tests for Concert Radar utility functions."""

from datetime import datetime, timezone

from custom_components.concert_radar.models import ConcertEvent
from custom_components.concert_radar.utils import (
    deduplicate_events,
    haversine,
    is_tribute_or_revival,
    km_to_miles,
    slugify_artist,
)


def test_haversine_known_distance():
    """Test haversine with known distance between London and Paris."""
    # London (51.5074, -0.1278) to Paris (48.8566, 2.3522) ~343 km
    distance = haversine(51.5074, -0.1278, 48.8566, 2.3522)
    assert 340 < distance < 350


def test_haversine_same_point():
    """Test haversine returns 0 for the same point."""
    distance = haversine(51.5074, -0.1278, 51.5074, -0.1278)
    assert distance == 0.0


def test_haversine_antipodal():
    """Test haversine for roughly antipodal points."""
    distance = haversine(0, 0, 0, 180)
    # Should be roughly half the Earth's circumference
    assert 20000 < distance < 20100


def test_slugify_artist_simple():
    """Test slugify with a simple name."""
    assert slugify_artist("Radiohead") == "radiohead"


def test_slugify_artist_spaces():
    """Test slugify with spaces."""
    assert slugify_artist("Massive Attack") == "massive_attack"


def test_slugify_artist_special_chars():
    """Test slugify with special characters."""
    assert slugify_artist("AC/DC") == "ac_dc"
    assert slugify_artist("Guns N' Roses") == "guns_n_roses"


def test_slugify_artist_leading_trailing():
    """Test slugify strips leading/trailing underscores."""
    assert slugify_artist("  The Band  ") == "the_band"


def test_km_to_miles():
    """Test km to miles conversion."""
    assert km_to_miles(100) == 62.1
    assert km_to_miles(0) == 0.0
    assert km_to_miles(1.60934) == 1.0


def _make_event(
    source: str, artist: str, date: str, city: str, event_id: str = "1"
) -> ConcertEvent:
    """Helper to create a ConcertEvent."""
    return ConcertEvent(
        event_id=event_id,
        source=source,
        artist=artist,
        event_date=datetime.fromisoformat(date),
        venue_name="Test Venue",
        venue_city=city,
        venue_country="GB",
        venue_latitude=51.5,
        venue_longitude=-0.1,
        distance_km=10.0,
    )


def test_deduplicate_events_no_duplicates():
    """Test dedup with no duplicates."""
    events = [
        _make_event("ticketmaster", "Radiohead", "2025-06-15T19:00:00", "London", "1"),
        _make_event("ticketmaster", "Radiohead", "2025-07-20T19:00:00", "Manchester", "2"),
    ]
    result = deduplicate_events(events)
    assert len(result) == 2


def test_deduplicate_events_with_duplicates():
    """Test dedup removes duplicates, preferring Ticketmaster."""
    events = [
        _make_event("bandsintown", "Radiohead", "2025-06-15T20:00:00", "London", "bit1"),
        _make_event("ticketmaster", "Radiohead", "2025-06-15T19:00:00", "London", "tm1"),
    ]
    result = deduplicate_events(events)
    assert len(result) == 1
    assert result[0].source == "ticketmaster"


def _make_tribute_event(artist: str, event_name: str | None = None) -> ConcertEvent:
    """Helper to create a ConcertEvent with a custom artist and event name."""
    return ConcertEvent(
        event_id="1",
        source="ticketmaster",
        artist=artist,
        event_date=datetime.fromisoformat("2025-06-15T19:00:00"),
        venue_name="Test Venue",
        venue_city="London",
        venue_country="GB",
        venue_latitude=51.5,
        venue_longitude=-0.1,
        distance_km=10.0,
        event_name=event_name,
    )


# --- is_tribute_or_revival ---

def test_tribute_keyword_in_artist_name():
    assert is_tribute_or_revival(_make_tribute_event("Tribute to Queen")) is True


def test_revival_keyword_in_artist_name():
    assert is_tribute_or_revival(_make_tribute_event("Queen Revival")) is True


def test_salute_keyword_in_artist_name():
    assert is_tribute_or_revival(_make_tribute_event("A Salute to AC/DC")) is True


def test_cover_band_keyword_in_artist_name():
    assert is_tribute_or_revival(_make_tribute_event("The Beatles Cover Band")) is True


def test_tribute_keyword_in_event_name():
    event = _make_tribute_event("Taylor Swift", "A Tribute to Taylor Swift")
    assert is_tribute_or_revival(event) is True


def test_revival_keyword_in_event_name():
    event = _make_tribute_event("Queen", "Queen Revival Night")
    assert is_tribute_or_revival(event) is True


def test_genuine_artist_no_event_name():
    assert is_tribute_or_revival(_make_tribute_event("Queen")) is False


def test_genuine_artist_with_innocent_event_name():
    event = _make_tribute_event("Radiohead", "Radiohead Live 2025")
    assert is_tribute_or_revival(event) is False


def test_case_insensitive_matching():
    assert is_tribute_or_revival(_make_tribute_event("QUEEN REVIVAL")) is True
    assert is_tribute_or_revival(_make_tribute_event("queen revival")) is True


def test_tribute_not_matched_as_substring():
    """'tribute' must match as a whole word, not inside another word."""
    event = _make_tribute_event("Distributive Jazz Trio")
    assert is_tribute_or_revival(event) is False


def test_deduplicate_events_sorted_by_date():
    """Test dedup returns events sorted by date."""
    events = [
        _make_event("ticketmaster", "Radiohead", "2025-08-01T19:00:00", "London", "3"),
        _make_event("ticketmaster", "Radiohead", "2025-06-15T19:00:00", "London", "1"),
        _make_event("ticketmaster", "Radiohead", "2025-07-01T19:00:00", "Manchester", "2"),
    ]
    result = deduplicate_events(events)
    assert len(result) == 3
    assert result[0].event_date < result[1].event_date < result[2].event_date
