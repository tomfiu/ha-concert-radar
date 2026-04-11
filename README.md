# Concert Radar for Home Assistant

[![HACS Default](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/tomfiu/ha-concert-radar.svg)](https://github.com/tomfiu/ha-concert-radar/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io)

**Never miss a concert from your favourite bands again.**

Concert Radar integrates live music event discovery directly into Home Assistant.
Tell it which artists you love and how far you're willing to travel — it'll do the rest,
alerting you the moment tickets go on sale, populating your HA calendar, and
exposing rich sensor data for powerful automations.

---

## Features

- **Track unlimited artists** — from global superstars to local indie bands
- **Geolocation radius search** — set your own distance threshold in km or miles
- **Native HA Calendar integration** — see all upcoming concerts in one view
- **Instant notifications** — HA events fire the moment a new concert is found
- **Ticket on-sale alerts** — dedicated event fires the instant tickets become available
- **Countdown sensors** — always know how many days until the next show
- **Weekly digest sensor** — a single markdown-ready summary of this week's concerts
- **API health sensor** — monitor whether API connections are working
- **Ticket links** — deep links directly to the ticketing page
- **Dual API coverage** — Ticketmaster + Bandsintown for maximum coverage
- **Automatic polling** — configurable interval (default: every 6 hours)
- **Exponential-backoff retries** — transient API failures are retried automatically
- **Tribute band filtering** — optionally ignore tribute, revival and cover acts
- **Ready-made automation blueprints** — install and go in seconds
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

### Per-artist entities

For each tracked artist Concert Radar creates:

| Entity | Type | Description |
|---|---|---|
| `sensor.concert_radar_{artist}_next_concert` | Sensor (timestamp) | Date/time of next nearby concert |
| `sensor.concert_radar_{artist}_upcoming_count` | Sensor | Number of upcoming concerts |
| `sensor.concert_radar_{artist}_venue` | Sensor | Venue name of the next concert |
| `sensor.concert_radar_{artist}_city` | Sensor | Location of next concert as `City, Country` |
| `sensor.concert_radar_{artist}_distance` | Sensor | Distance from home to next concert (km or mi) |
| `sensor.concert_radar_{artist}_days_until_concert` | Sensor | Days until the next concert |
| `binary_sensor.concert_radar_{artist}_has_nearby_concert` | Binary Sensor | `on` if any concert is nearby |
| `binary_sensor.concert_radar_{artist}_tickets_on_sale` | Binary Sensor | `on` when tickets for the next concert are on sale |

### Global entities

| Entity | Type | Description |
|---|---|---|
| `sensor.concert_radar_next_concert_overall` | Sensor (timestamp) | Soonest upcoming concert across all artists |
| `sensor.concert_radar_total_upcoming` | Sensor | Total concerts across all artists |
| `sensor.concert_radar_weekly_digest` | Sensor | Count of concerts in the next 7 days; `digest` attribute holds a formatted markdown summary |
| `sensor.concert_radar_last_updated` | Sensor (timestamp) | Last API poll timestamp |
| `binary_sensor.concert_radar_any_nearby_concert` | Binary Sensor | `on` if any artist has a nearby concert |
| `binary_sensor.concert_radar_api_healthy` | Binary Sensor | `on` when the last API update succeeded |
| `calendar.concert_radar` | Calendar | All upcoming concerts in calendar view |

### Key sensor attributes

The `_next_concert` and `_next_concert_overall` sensors expose these attributes for automations and cards:

| Attribute | Description |
|---|---|
| `artist` | Artist name |
| `event_name` | Full event name |
| `venue_name` | Venue name |
| `venue_city` / `venue_country` | Location |
| `venue_latitude` / `venue_longitude` | Venue coordinates (for map cards) |
| `distance_km` / `distance_mi` | Distance from home |
| `days_until` | Integer days until the event |
| `ticket_url` | Direct link to tickets |
| `event_image_url` | Event artwork URL |
| `on_sale` | Whether tickets are currently on sale |
| `price_min` / `price_max` / `currency` | Ticket price range |
| `source` | Data source (`ticketmaster` or `bandsintown`) |

---

## Automation Blueprints

Concert Radar ships with ready-made blueprints in `blueprints/automation/concert_radar/`.
Import them via **Settings** > **Automations & Scenes** > **Blueprints** > **Import Blueprint**.

| Blueprint | Trigger | What it does |
|---|---|---|
| `concert_ticket_reminder.yaml` | N days before a concert | Sends a notification N days before a tracked artist's next show |
| `on_sale_alert.yaml` | Tickets go on sale | Notifies you the instant tickets become available (optional artist filter) |
| `weekly_digest.yaml` | Configurable day & time | Sends a weekly markdown summary of upcoming concerts |

---

## Automations

### New concert push notification

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
        Playing at {{ trigger.event.data.venue_name }},
        {{ trigger.event.data.venue_city }}
        on {{ trigger.event.data.event_date | as_timestamp | timestamp_custom('%B %d, %Y') }}
        — {{ trigger.event.data.distance_km | round(0) }} km away
      data:
        url: "{{ trigger.event.data.ticket_url }}"
```

### Tickets on sale alert

```yaml
alias: "Concert Radar — On Sale Alert"
trigger:
  - platform: event
    event_type: concert_radar_ticket_sale_starts
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Tickets on sale: {{ trigger.event.data.artist }}!"
      message: >
        {{ trigger.event.data.artist }} at {{ trigger.event.data.venue_name }},
        {{ trigger.event.data.venue_city }}
        on {{ trigger.event.data.event_date | as_timestamp | timestamp_custom('%B %d, %Y') }}
        ({{ trigger.event.data.days_until }} days away).
        {% if trigger.event.data.price_min %}
        From {{ trigger.event.data.price_min }} {{ trigger.event.data.currency }}.
        {% endif %}
        {{ trigger.event.data.ticket_url }}
```

### Remind me 7 days before a concert

```yaml
alias: "Concert Radar — 7-day Reminder"
trigger:
  - platform: numeric_state
    entity_id: sensor.concert_radar_radiohead_days_until_concert
    below: 8
    above: 0
condition:
  - condition: template
    value_template: "{{ now().hour == 9 and now().minute < 5 }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Concert in {{ states('sensor.concert_radar_radiohead_days_until_concert') }} days!"
      message: >
        {{ state_attr('sensor.concert_radar_radiohead_days_until_concert', 'artist') }}
        at {{ state_attr('sensor.concert_radar_radiohead_days_until_concert', 'venue_name') }},
        {{ state_attr('sensor.concert_radar_radiohead_days_until_concert', 'venue_city') }}
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

### Weekly digest notification (Sunday 18:00)

```yaml
alias: "Concert Radar — Weekly Digest"
trigger:
  - platform: time
    at: "18:00:00"
condition:
  - condition: template
    value_template: "{{ now().weekday() == 6 }}"
  - condition: numeric_state
    entity_id: sensor.concert_radar_weekly_digest
    above: 0
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "🎵 Your Weekly Concert Digest"
      message: "{{ state_attr('sensor.concert_radar_weekly_digest', 'digest') }}"
```

### Dashboard Markdown Card

```yaml
type: markdown
content: >
  {{ state_attr('sensor.concert_radar_weekly_digest', 'digest') }}
```

Or for a single artist:

```yaml
type: markdown
content: >
  ## Next Concert

  {% set s = states.sensor.concert_radar_radiohead_next_concert %}
  {% if s.state not in ['unknown', 'unavailable'] %}
  **{{ s.attributes.artist }}** at **{{ s.attributes.venue_name }}**
  {{ states('sensor.concert_radar_radiohead_city') }}
  — {{ states('sensor.concert_radar_radiohead_distance') }} away
  — **{{ states('sensor.concert_radar_radiohead_days_until_concert') }} days to go**
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

| Event | When it fires | Key payload fields |
|---|---|---|
| `concert_radar_new_concert` | A new concert is discovered | `artist`, `event_name`, `event_date`, `venue_name`, `venue_city`, `venue_country`, `distance_km`, `distance_mi`, `ticket_url`, `source`, `lineup` |
| `concert_radar_artist_on_tour` | A tracked artist goes from no events → has events | `artist`, `concert_count`, `next_concert_date` |
| `concert_radar_ticket_sale_starts` | Tickets transition to on-sale on a known event | `artist`, `event_name`, `event_date`, `venue_name`, `venue_city`, `ticket_url`, `days_until`, `price_min`, `currency` |

---

## Troubleshooting

**No concerts showing up?**

- Check your Ticketmaster API key is valid (**Settings** > **Integrations** > **Concert Radar** > **Configure**)
- Try increasing your search radius
- Some artists may not be listed on Ticketmaster — Bandsintown fallback handles most of these
- If **Ignore tribute, revival and cover bands** is enabled, genuine concerts won't be filtered — but double-check the option if results seem unexpectedly empty
- Run `concert_radar.refresh` to force an immediate poll
- Check `Settings` > `System` > `Logs` for any Concert Radar errors

**`binary_sensor.concert_radar_api_healthy` is `off`?**

- Check HA logs for connection errors or rate-limit warnings
- Verify your Ticketmaster API key is still valid
- Concert Radar automatically retries transient failures with exponential backoff (2 s → 4 s → 8 s); persistent `off` indicates a lasting issue

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
