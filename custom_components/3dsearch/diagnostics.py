"""Diagnostics download: the API key, the account and other personal details are removed."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY
from .coordinator import ThreeDSearchConfigEntry

# People attach this file to public GitHub issues. async_redact_data works by key at every level, so this also covers
# printers and spools; provider, model, firmware, state and slots stay, and those are what a bug report needs.
TO_REDACT = {
    CONF_API_KEY, "id", "name", "display_name", "email", "user", "user_id", "username",
    "image", "location", "printer", "title",
}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ThreeDSearchConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = dict(entry.runtime_data.data)
    # Printers and spools are stored by id, and async_redact_data only looks at values. A Bambu Lab id is the serial number.
    data["printers"] = list(data.get("printers", {}).values())
    data["spool_items"] = list(data.get("spool_items", {}).values())
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "data": async_redact_data(data, TO_REDACT),
    }
