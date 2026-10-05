"""3DSEARCH Printers & Filament — printers, slots and spool stock from 3dsearch.net."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ThreeDSearchApi
from .const import CONF_API_KEY
from .coordinator import ThreeDSearchConfigEntry, ThreeDSearchCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.EVENT, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ThreeDSearchConfigEntry) -> bool:
    """Set up 3DSEARCH from a config entry."""
    api = ThreeDSearchApi(async_get_clientsession(hass), entry.data[CONF_API_KEY])
    coordinator = ThreeDSearchCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ThreeDSearchConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(hass: HomeAssistant, entry: ThreeDSearchConfigEntry) -> None:
    """Apply a new polling interval."""
    await hass.config_entries.async_reload(entry.entry_id)
