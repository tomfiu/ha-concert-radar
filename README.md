# Concert Radar for Home Assistant

[![HACS Default](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/tomfiu/ha-concert-radar.svg)](https://github.com/tomfiu/ha-concert-radar/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io)

**Never miss a concert from your favourite bands again.**

Concert Radar integrates live music event discovery directly into Home Assistant.
Tell it which artists you love and how far you're willing to travel — it'll do the rest,
alerting you the moment a ticket goes on sale, populating your HA calendar, and
exposing rich sensor data for powerful automations.

---

## Features

- **Track unlimited artists** — from global superstars to local indie bands
- **Geolocation radius search** — set your own distance threshold in km or miles
- **Native HA Calendar integration** — see all upcoming concerts in one view
- **Instant notifications** — HA events fire the moment a new concert is found
- **Ticket links** — deep links directly to the ticketing page
- **Dual API coverage** — Ticketmaster + Bandsintown for maximum coverage
- **Automatic polling** — configurable interval (default: every 6 hours)
- **Tribute band filtering** — optionally ignore tribute, revival and cover acts
- **Fully UI configurable** — no YAML required
- **100% free** — uses free-tier APIs only

---

## Prerequisites

1. A free [Ticketmaster Developer](https://developer.ticketmaster.com/) account and API key
   - Takes ~2 minutes to register
   - Free tier: 5,000 calls/day (more than enough)
2. [HACS](https://hacs.xyz) installed in your Home Assistant instance

---

## Installation

### Via HACS (recommended)

1. Open HACS in your Home Assistant sidebar
2. Click **Integrations** > **Explore & Download Repositories**
3. Search for **Concert Radar**
4. Click **Download**
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/concert_radar` folder to your HA `custom_components` directory
2. Restart Home Assistant

---

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for **Concert Radar**
3. Enter your **Ticketmaster API key**
4. Enter your **artists** (comma separated, e.g. `Radiohead, Massive Attack, Portishead`)
5. Set your **search radius** (default: 150 km)
6. Choose whether to use your HA home location (recommended)
7. Click **Finish**

Concert Radar will perform an initial scan immediately after setup.

### Options

All settings can be updated later via **Settings** > **Integrations** > **Concert Radar** > **Configure**.

| Option | Default | Description |
|---|---|---|
| Artists | — | Comma-separated list of artists to track |
| Search radius | 150 km | Maximum distance from your location |
| Radius unit | km | `km` or `mi` |
| Poll interval | 6 h | How often to check for new events |
| Lookahead window | 180 days | How far into the future to search |
| Enable persistent notifications | on | Show an in-app notification for each new concert |
| Ignore tribute, revival and cover bands | off | Filter out tribute acts (e.g. "Queen Revival", "Tribute to Taylor Swift") |

---

## Entities

For each tracked artist, the following entities are created:

| Entity | Type | Description |
|---|---|---|
| `sensor.concert_radar_{artist}_next_concert` | Sensor | Date/time of next nearby concert |
| `sensor.concert_radar_{artist}_upcoming_count` | Sensor | Number of upcoming concerts |
| `binary_sensor.concert_radar_{artist}_has_nearby_concert` | Binary Sensor | `on` if any concert nearby |

Plus global entities:

| Entity | Type | Description |
|---|---|---|
| `sensor.concert_radar_total_upcoming` | Sensor | Total concerts across all artists |
| `sensor.concert_radar_last_updated` | Sensor | Last API poll timestamp |
| `binary_sensor.concert_radar_any_nearby_concert` | Binary Sensor | `on` if any artist has a nearby concert |
| `calendar.concert_radar` | Calendar | All upcoming concerts in calendar view |

---

## Automations

### Get a push notification for every new concert

```yaml
alias: "Concert Radar — Push Notification"
trigger:
  - platform: event
    event_type: concert_radar_new_concert
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "{{ trigger.event.data.artist }} Concert Alert!"
      message: >
        Playing at {{ trigger.event.data.venue_name }}, {{ trigger.event.data.venue_city }}
        on {{ trigger.event.data.event_date | as_timestamp | timestamp_custom('%B %d, %Y') }}
        — {{ trigger.event.data.distance_km | round(0) }}km away
      data:
        url: "{{ trigger.event.data.ticket_url }}"
```

### Flash lights when a new concert is found

```yaml
alias: "Concert Radar — Flash Lights"
trigger:
  - platform: event
    event_type: concert_radar_new_concert
action:
  - repeat:
      count: 3
      sequence:
        - service: light.turn_on
          target:
            entity_id: light.living_room
          data:
            color_name: purple
            brightness: 255
        - delay: "00:00:00.5"
        - service: light.turn_off
          target:
            entity_id: light.living_room
        - delay: "00:00:00.5"
```

### Dashboard Markdown Card

```yaml
type: markdown
content: >
  ## Next Concert

  {% set artist = "radiohead" %}
  {% set s = states.sensor["concert_radar_" + artist + "_next_concert"] %}
  {% if s.state != "unknown" %}
  **{{ s.attributes.artist }}** at **{{ s.attributes.venue_name }}**
  {{ s.attributes.venue_city }} — {{ s.attributes.distance_km | round(1) }} km away
  {{ s.state | as_timestamp | timestamp_custom('%A, %B %d %Y at %H:%M') }}
  {% if s.attributes.price_min %}
  From {{ s.attributes.price_min }} {{ s.attributes.currency }}
  {% endif %}
  [Get Tickets]({{ s.attributes.ticket_url }})
  {% else %}
  No upcoming concerts nearby. Stay tuned!
  {% endif %}
```

---

## Services

| Service | Description |
|---|---|
| `concert_radar.refresh` | Manually trigger a data refresh |
| `concert_radar.add_artist` | Add a new artist to track |
| `concert_radar.remove_artist` | Remove a tracked artist |

---

## Events

| Event | Description |
|---|---|
| `concert_radar_new_concert` | Fired for each newly discovered concert |
| `concert_radar_artist_on_tour` | Fired when a tracked artist starts touring nearby |

---

## Troubleshooting

**No concerts showing up?**

- Check your Ticketmaster API key is valid (Settings > Integrations > Concert Radar > Configure)
- Try increasing your search radius
- Some artists may not be listed on Ticketmaster — Bandsintown fallback handles most of these
- If **Ignore tribute, revival and cover bands** is enabled, genuine concerts won't be filtered — but double-check the option if results seem unexpectedly empty
- Run `concert_radar.refresh` to force an immediate poll
- Check `Settings > System > Logs` for any Concert Radar errors

**API rate limit errors?**

- The default 6-hour poll interval uses ~4 API calls per artist per day
- With 5,000 free daily calls, you can track ~1,000 artists before hitting limits

---

## License

MIT License — see [LICENSE](LICENSE) for details.

## Acknowledgements

- [Ticketmaster Discovery API](https://developer.ticketmaster.com/)
- [Bandsintown Public API](https://rest.bandsintown.com/)
- [Home Assistant](https://www.home-assistant.io/)
- [HACS](https://hacs.xyz/)
