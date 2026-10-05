"""Polls the 3DSEARCH endpoint and keeps the latest state for all entities."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ThreeDSearchApi, ThreeDSearchAuthError, ThreeDSearchError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type ThreeDSearchConfigEntry = ConfigEntry[ThreeDSearchCoordinator]


class ThreeDSearchCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """One request per interval returns every printer and the spool stock."""

    config_entry: ThreeDSearchConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ThreeDSearchConfigEntry, api: ThreeDSearchApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.status()
        except ThreeDSearchAuthError as err:
            raise ConfigEntryAuthFailed(translation_domain=DOMAIN, translation_key="auth_failed") from err
        except ThreeDSearchError as err:
            raise UpdateFailed(translation_domain=DOMAIN, translation_key="update_failed",
                               translation_placeholders={"error": err.code}) from err
        printers = {str(p["id"]): p for p in data.get("printers", []) if isinstance(p, dict) and p.get("id")}
        return {
            "account": data.get("account") or {},
            "printers": printers,
            "spools": data.get("spools") or {},
            "time": data.get("time"),
        }

    @property
    def account_id(self) -> str:
        """Stable id of the 3DSEARCH account (also the config entry unique id)."""
        return str((self.data or {}).get("account", {}).get("id", self.config_entry.unique_id))

    def printer(self, printer_id: str) -> dict[str, Any] | None:
        """Latest data of one printer, None if it is gone."""
        return (self.data or {}).get("printers", {}).get(printer_id)
