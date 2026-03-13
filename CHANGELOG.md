# Changelog

## [1.0.0] - 2025-03-13

### Added

- Initial release
- Track multiple artists/bands for upcoming concerts
- Dual API support: Ticketmaster Discovery API + Bandsintown
- Geo-radius search with configurable distance (km/miles)
- Per-artist sensors: next concert, upcoming count, has nearby concert
- Global sensors: total upcoming, last updated, any nearby concert
- Native Home Assistant calendar entity
- HA event bus integration (concert_radar_new_concert, concert_radar_artist_on_tour)
- Persistent notifications for newly discovered concerts
- Services: refresh, add_artist, remove_artist
- Full UI configuration flow with options editing
- HACS compatible
