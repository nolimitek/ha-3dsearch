"""Diagnostics download (the API key is removed)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY
from .coordinator import ThreeDSearchConfigEntry


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ThreeDSearchConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return {
        "entry": async_redact_data(dict(entry.data), {CONF_API_KEY}),
        "options": dict(entry.options),
        "data": entry.runtime_data.data,
    }
