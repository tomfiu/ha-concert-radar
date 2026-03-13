"""Config flow for Concert Radar integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.ticketmaster import TicketmasterClient
from .const import (
    CONF_ARTISTS,
    CONF_BIT_APP_ID,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_LOOKAHEAD_DAYS,
    CONF_NOTIFICATIONS,
    CONF_POLL_INTERVAL,
    CONF_RADIUS,
    CONF_RADIUS_UNIT,
    CONF_TM_API_KEY,
    CONF_USE_HA_LOCATION,
    DEFAULT_BANDSINTOWN_APP_ID,
    DEFAULT_LOOKAHEAD_DAYS,
    DEFAULT_POLL_INTERVAL_HOURS,
    DEFAULT_RADIUS_KM,
    DEFAULT_RADIUS_UNIT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ConcertRadarConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Concert Radar."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api_data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> ConcertRadarOptionsFlow:
        """Get the options flow for this handler."""
        return ConcertRadarOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle step 1: API keys."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the Ticketmaster API key
            session = async_get_clientsession(self.hass)
            client = TicketmasterClient(
                api_key=user_input[CONF_TM_API_KEY], session=session
            )
            valid = await client.validate_api_key()
            if not valid:
                errors["base"] = "invalid_api_key"
            else:
                self._api_data = user_input
                return await self.async_step_artists()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TM_API_KEY): str,
                    vol.Optional(
                        CONF_BIT_APP_ID, default=DEFAULT_BANDSINTOWN_APP_ID
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_artists(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle step 2: Artists and location."""
        errors: dict[str, str] = {}

        if user_input is not None:
            artists_str = user_input.get(CONF_ARTISTS, "")
            artists = [a.strip() for a in artists_str.split(",") if a.strip()]

            if not artists:
                errors[CONF_ARTISTS] = "no_artists"
            else:
                data = {
                    **self._api_data,
                    CONF_ARTISTS: artists,
                    CONF_RADIUS: user_input.get(CONF_RADIUS, DEFAULT_RADIUS_KM),
                    CONF_RADIUS_UNIT: user_input.get(
                        CONF_RADIUS_UNIT, DEFAULT_RADIUS_UNIT
                    ),
                    CONF_USE_HA_LOCATION: user_input.get(CONF_USE_HA_LOCATION, True),
                    CONF_POLL_INTERVAL: user_input.get(
                        CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL_HOURS
                    ),
                    CONF_NOTIFICATIONS: user_input.get(CONF_NOTIFICATIONS, True),
                    CONF_LOOKAHEAD_DAYS: user_input.get(
                        CONF_LOOKAHEAD_DAYS, DEFAULT_LOOKAHEAD_DAYS
                    ),
                }

                if not user_input.get(CONF_USE_HA_LOCATION, True):
                    data[CONF_LATITUDE] = user_input.get(CONF_LATITUDE)
                    data[CONF_LONGITUDE] = user_input.get(CONF_LONGITUDE)

                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Concert Radar",
                    data=data,
                )

        return self.async_show_form(
            step_id="artists",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ARTISTS): str,
                    vol.Optional(CONF_RADIUS, default=DEFAULT_RADIUS_KM): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=1000)
                    ),
                    vol.Optional(
                        CONF_RADIUS_UNIT, default=DEFAULT_RADIUS_UNIT
                    ): vol.In(["km", "mi"]),
                    vol.Optional(CONF_USE_HA_LOCATION, default=True): bool,
                    vol.Optional(CONF_LATITUDE): vol.Coerce(float),
                    vol.Optional(CONF_LONGITUDE): vol.Coerce(float),
                    vol.Optional(
                        CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL_HOURS
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=48)),
                    vol.Optional(CONF_NOTIFICATIONS, default=True): bool,
                    vol.Optional(
                        CONF_LOOKAHEAD_DAYS, default=DEFAULT_LOOKAHEAD_DAYS
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=365)),
                }
            ),
            errors=errors,
        )


class ConcertRadarOptionsFlow(OptionsFlow):
    """Handle options flow for Concert Radar."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            artists_str = user_input.get(CONF_ARTISTS, "")
            artists = [a.strip() for a in artists_str.split(",") if a.strip()]

            if not artists:
                errors[CONF_ARTISTS] = "no_artists"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_ARTISTS: artists,
                        CONF_RADIUS: user_input.get(CONF_RADIUS, DEFAULT_RADIUS_KM),
                        CONF_RADIUS_UNIT: user_input.get(
                            CONF_RADIUS_UNIT, DEFAULT_RADIUS_UNIT
                        ),
                        CONF_POLL_INTERVAL: user_input.get(
                            CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL_HOURS
                        ),
                        CONF_NOTIFICATIONS: user_input.get(CONF_NOTIFICATIONS, True),
                        CONF_LOOKAHEAD_DAYS: user_input.get(
                            CONF_LOOKAHEAD_DAYS, DEFAULT_LOOKAHEAD_DAYS
                        ),
                    },
                )

        current = {**self._config_entry.data, **self._config_entry.options}
        artists_default = ", ".join(current.get(CONF_ARTISTS, []))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ARTISTS, default=artists_default): str,
                    vol.Optional(
                        CONF_RADIUS,
                        default=current.get(CONF_RADIUS, DEFAULT_RADIUS_KM),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1000)),
                    vol.Optional(
                        CONF_RADIUS_UNIT,
                        default=current.get(CONF_RADIUS_UNIT, DEFAULT_RADIUS_UNIT),
                    ): vol.In(["km", "mi"]),
                    vol.Optional(
                        CONF_POLL_INTERVAL,
                        default=current.get(
                            CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL_HOURS
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=48)),
                    vol.Optional(
                        CONF_NOTIFICATIONS,
                        default=current.get(CONF_NOTIFICATIONS, True),
                    ): bool,
                    vol.Optional(
                        CONF_LOOKAHEAD_DAYS,
                        default=current.get(
                            CONF_LOOKAHEAD_DAYS, DEFAULT_LOOKAHEAD_DAYS
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=365)),
                }
            ),
            errors=errors,
        )
