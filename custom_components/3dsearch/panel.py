"""Sidebar panel "3D printing": the 3DSEARCH workshop (printers, spools, slicer, print queue) inside Home Assistant.

The panel shows https://3dsearch.net/filament/embed.php in a frame. It signs in with a short-lived token that the
integration fetches with the API key (websocket command 3dsearch/embed), so the API key never reaches the browser and
no 3dsearch.net cookie is needed — Safari and the iOS companion app block those in frames anyway.
Only accounts that 3dsearch.net unlocks for it get the panel (features.panel, currently a test).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .api import ThreeDSearchError
from .const import DOMAIN


PANEL_URL_PATH = "3dsearch"
PANEL_JS_URL = "/3dsearch/3dsearch-panel.js"
PANEL_FILE = Path(__file__).parent / "frontend" / "3dsearch-panel.js"
PANEL_ICON = "mdi:printer-3d"
# The sidebar title is a plain string (no translation keys), so it follows the language Home Assistant runs in
TITLES = {"de": "3D-Druck", "en": "3D printing", "fr": "Impression 3D", "es": "Impresión 3D", "it": "Stampa 3D", "nl": "3D-printen"}
DATA_PANEL = f"{DOMAIN}_panel_entry"


def panel_title(hass: HomeAssistant) -> str:
    """Sidebar title in the language of Home Assistant."""
    return TITLES.get((hass.config.language or "en").split("-")[0], TITLES["en"])


async def async_setup_panel(hass: HomeAssistant, entry_id: str, version: str) -> None:
    """Add the sidebar entry for this config entry (one per Home Assistant, the first account that may use it)."""
    if "frontend" not in hass.config.components or hass.data.get(DATA_PANEL):
        return
    from homeassistant.components import panel_custom  # noqa: PLC0415

    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name="threedsearch-panel",
        sidebar_title=panel_title(hass),
        sidebar_icon=PANEL_ICON,
        module_url=f"{PANEL_JS_URL}?v={version}",
        config={"entry_id": entry_id},
        require_admin=True,
    )
    hass.data[DATA_PANEL] = entry_id


@callback
def async_remove_panel(hass: HomeAssistant, entry_id: str) -> None:
    """Remove the sidebar entry when the config entry that owns it unloads."""
    if hass.data.get(DATA_PANEL) != entry_id:
        return
    from homeassistant.components import frontend  # noqa: PLC0415

    frontend.async_remove_panel(hass, PANEL_URL_PATH, warn_if_unknown=False)
    hass.data.pop(DATA_PANEL, None)


@websocket_api.websocket_command({vol.Required("type"): "3dsearch/embed", vol.Required("entry_id"): str})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_embed(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Fetch a short-lived sign-in for the embedded workshop."""
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN or not hasattr(entry, "runtime_data"):
        connection.send_error(msg["id"], "not_found", "3DSEARCH entry not loaded")
        return
    try:
        result = await entry.runtime_data.api.embed_token()
    except ThreeDSearchError as err:
        connection.send_error(msg["id"], "embed_failed", err.code)
        return
    if not isinstance(result.get("token"), str) or not isinstance(result.get("url"), str):
        connection.send_error(msg["id"], "embed_failed", "bad_response")
        return
    connection.send_result(msg["id"], {"url": result["url"], "token": result["token"], "expires_in": result.get("expires_in")})


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    """Register the websocket command once."""
    websocket_api.async_register_command(hass, ws_embed)

