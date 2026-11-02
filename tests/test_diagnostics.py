"""Diagnostics end up in public GitHub issues: nothing that identifies the account or a printer may be in them."""

from __future__ import annotations

from importlib import import_module
import json

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import API_URL, DOMAIN, KEY

diagnostics = import_module(f"custom_components.{DOMAIN}.diagnostics")


async def _diagnostics(hass: HomeAssistant, aioclient_mock, payload) -> dict:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="1", data={"api_key": KEY}, title="3DSEARCH (Tester)")
    entry.add_to_hass(hass)
    aioclient_mock.get(API_URL, json=payload)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return await diagnostics.async_get_config_entry_diagnostics(hass, entry)


async def test_personal_data_is_removed(hass: HomeAssistant, aioclient_mock, payload) -> None:
    payload["account"]["email"] = "someone@example.com"
    payload["spools"]["items"][0]["location"] = "Shelf"
    result = await _diagnostics(hass, aioclient_mock, payload)
    dumped = json.dumps(result)
    for secret in (KEY, "Tester", "someone@example.com", "a3c12bb1ca4ea642", "01P00A123", "Printsaurus", "cdn.example",
                   "Shelf", "Benchy"):
        assert secret not in dumped, secret
    assert result["entry"]["api_key"] == "**REDACTED**"
    assert result["data"]["account"] == {"id": "**REDACTED**", "name": "**REDACTED**", "email": "**REDACTED**"}


async def test_useful_data_stays(hass: HomeAssistant, aioclient_mock, payload) -> None:
    result = await _diagnostics(hass, aioclient_mock, payload)
    first = result["data"]["printers"][0]
    assert isinstance(result["data"]["printers"], list)
    assert first["provider"] == "moonraker" and first["model"] == "Anycubic Kobra S1" and first["state"] == "printing"
    assert first["fw"] == "Rinkhals 20260716_02" and first["slots"]
    assert result["data"]["features"] == payload.get("features", {})
