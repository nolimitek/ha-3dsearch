"""Config flow: paste a personal API key from 3dsearch.net (Printers & Filament → Settings → Home Assistant)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import ThreeDSearchApi, ThreeDSearchAuthError, ThreeDSearchError
from .const import (
    CONF_API_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    SITE_URL,
)

KEY_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))})
PLACEHOLDERS = {"settings_url": f"{SITE_URL}#settings"}


class ThreeDSearchConfigFlow(ConfigFlow, domain=DOMAIN):
    """One entry per 3DSEARCH account."""

    VERSION = 1

    async def _check(self, key: str) -> tuple[dict[str, Any] | None, dict[str, str]]:
        """Validate the key against the server; returns (status, errors)."""
        if not key.strip().startswith("3ds_"):
            return None, {CONF_API_KEY: "invalid_key"}
        try:
            data = await ThreeDSearchApi(async_get_clientsession(self.hass), key).status()
        except ThreeDSearchAuthError as err:
            return None, {"base": "not_allowed" if err.code == "not_allowed" else "invalid_key"}
        except ThreeDSearchError:
            return None, {"base": "cannot_connect"}
        return data, {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data, errors = await self._check(user_input[CONF_API_KEY])
            if data:
                account = data.get("account") or {}
                await self.async_set_unique_id(str(account.get("id")))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"3DSEARCH ({account.get('name')})" if account.get("name") else "3DSEARCH",
                    data={CONF_API_KEY: user_input[CONF_API_KEY].strip()},
                )
        return self.async_show_form(step_id="user", data_schema=KEY_SCHEMA, errors=errors, description_placeholders=PLACEHOLDERS)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """The key was revoked or deleted."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data, errors = await self._check(user_input[CONF_API_KEY])
            if data:
                await self.async_set_unique_id(str((data.get("account") or {}).get("id")))
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data_updates={CONF_API_KEY: user_input[CONF_API_KEY].strip()}
                )
        return self.async_show_form(step_id="reauth_confirm", data_schema=KEY_SCHEMA, errors=errors,
                                    description_placeholders=PLACEHOLDERS)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> ThreeDSearchOptionsFlow:
        return ThreeDSearchOptionsFlow()


class ThreeDSearchOptionsFlow(OptionsFlow):
    """Polling interval."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])})
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_SCAN_INTERVAL, default=current): NumberSelector(NumberSelectorConfig(
                    min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL, step=10, unit_of_measurement="s", mode=NumberSelectorMode.BOX)),
            }),
        )
