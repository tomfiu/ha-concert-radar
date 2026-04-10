"""Constants for the Concert Radar integration."""

DOMAIN = "concert_radar"
PLATFORMS = ["sensor", "binary_sensor", "calendar"]

DEFAULT_RADIUS_KM = 150
DEFAULT_POLL_INTERVAL_HOURS = 6
DEFAULT_LOOKAHEAD_DAYS = 180
DEFAULT_BANDSINTOWN_APP_ID = "concert_radar"
DEFAULT_RADIUS_UNIT = "km"
DEFAULT_IGNORE_TRIBUTE_BANDS = False
DEFAULT_BAND_IGNORE_LIST: list[str] = []

CONF_ARTISTS = "artists"
CONF_RADIUS = "radius"
CONF_RADIUS_UNIT = "radius_unit"
CONF_TM_API_KEY = "tm_api_key"
CONF_BIT_APP_ID = "bit_app_id"
CONF_POLL_INTERVAL = "poll_interval"
CONF_USE_HA_LOCATION = "use_ha_location"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_NOTIFICATIONS = "notifications"
CONF_LOOKAHEAD_DAYS = "lookahead_days"
CONF_IGNORE_TRIBUTE_BANDS = "ignore_tribute_bands"
CONF_BAND_IGNORE_LIST = "band_ignore_list"

EVENT_NEW_CONCERT = "concert_radar_new_concert"
EVENT_ARTIST_ON_TOUR = "concert_radar_artist_on_tour"
EVENT_TICKET_SALE_STARTS = "concert_radar_ticket_sale_starts"

ATTR_ARTIST = "artist"
ATTR_EVENT_NAME = "event_name"
ATTR_VENUE_NAME = "venue_name"
ATTR_VENUE_CITY = "venue_city"
ATTR_VENUE_COUNTRY = "venue_country"
ATTR_VENUE_LATITUDE = "venue_latitude"
ATTR_VENUE_LONGITUDE = "venue_longitude"
ATTR_DISTANCE_KM = "distance_km"
ATTR_DISTANCE_MI = "distance_mi"
ATTR_TICKET_URL = "ticket_url"
ATTR_EVENT_IMAGE_URL = "event_image_url"
ATTR_DAYS_UNTIL = "days_until"
ATTR_ON_SALE = "on_sale"
ATTR_PRICE_MIN = "price_min"
ATTR_PRICE_MAX = "price_max"
ATTR_CURRENCY = "currency"
ATTR_SOURCE = "source"
ATTR_CONCERTS = "concerts"
ATTR_LAST_UPDATED = "last_updated"
ATTR_DISTANCE_UNIT = "unit"
ATTR_LINEUP = "lineup"
