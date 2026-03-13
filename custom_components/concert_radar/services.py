"""Service handlers for Concert Radar."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall

from .const import CONF_ARTISTS, DOMAIN
from .coordinator import ConcertRadarCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_REFRESH = "refresh"
SERVICE_ADD_ARTIST = "add_artist"
SERVICE_REMOVE_ARTIST = "remove_artist"


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up Concert Radar services."""

    async def _get_coordinator() -> ConcertRadarCoordinator | None:
        """Get the first coordinator instance."""
        if DOMAIN not in hass.data:
            return None
        for coordinator in hass.data[DOMAIN].values():
            if isinstance(coordinator, ConcertRadarCoordinator):
                return coordinator
        return None

    async def handle_refresh(call: ServiceCall) -> None:
        """Handle the refresh service call."""
        coordinator = await _get_coordinator()
        if coordinator:
            await coordinator.async_request_refresh()
        else:
            _LOGGER.warning("No Concert Radar coordinator found")

    async def handle_add_artist(call: ServiceCall) -> None:
        """Handle the add_artist service call."""
        artist = call.data["artist"]
        coordinator = await _get_coordinator()
        if not coordinator:
            _LOGGER.warning("No Concert Radar coordinator found")
            return

        current_artists = list(coordinator.config_entry.options.get(
            CONF_ARTISTS,
            coordinator.config_entry.data.get(CONF_ARTISTS, []),
        ))

        if artist not in current_artists:
            current_artists.append(artist)
            new_options = {**coordinator.config_entry.options, CONF_ARTISTS: current_artists}
            hass.config_entries.async_update_entry(
                coordinator.config_entry, options=new_options
            )
            _LOGGER.info("Added artist '%s' to Concert Radar", artist)
        else:
            _LOGGER.info("Artist '%s' already tracked", artist)

    async def handle_remove_artist(call: ServiceCall) -> None:
        """Handle the remove_artist service call."""
        artist = call.data["artist"]
        coordinator = await _get_coordinator()
        if not coordinator:
            _LOGGER.warning("No Concert Radar coordinator found")
            return

        current_artists = list(coordinator.config_entry.options.get(
            CONF_ARTISTS,
            coordinator.config_entry.data.get(CONF_ARTISTS, []),
        ))

        if artist in current_artists:
            current_artists.remove(artist)
            new_options = {**coordinator.config_entry.options, CONF_ARTISTS: current_artists}
            hass.config_entries.async_update_entry(
                coordinator.config_entry, options=new_options
            )
            _LOGGER.info("Removed artist '%s' from Concert Radar", artist)
        else:
            _LOGGER.warning("Artist '%s' not found in tracked artists", artist)

    hass.services.async_register(DOMAIN, SERVICE_REFRESH, handle_refresh)
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_ARTIST,
        handle_add_artist,
        schema=vol.Schema({vol.Required("artist"): str}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_ARTIST,
        handle_remove_artist,
        schema=vol.Schema({vol.Required("artist"): str}),
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Concert Radar services."""
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
    hass.services.async_remove(DOMAIN, SERVICE_ADD_ARTIST)
    hass.services.async_remove(DOMAIN, SERVICE_REMOVE_ARTIST)
