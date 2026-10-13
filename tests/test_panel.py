"""Sidebar panel "3D printing": only for accounts 3dsearch.net unlocked, short-lived sign-in only for admins."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import API_URL, DOMAIN, KEY

EMBED = {"token": "emb_" + "c3" * 24, "expires_in": 43200, "url": "https://3dsearch.net/filament/embed.php"}


async def _setup(hass: HomeAssistant, aioclient_mock, payload) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="1", data={"api_key": KEY})
    entry.add_to_hass(hass)
    aioclient_mock.get(API_URL, json=payload)
    aioclient_mock.post(API_URL, json=EMBED)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_panel_only_when_unlocked(hass: HomeAssistant, aioclient_mock, payload) -> None:
    hass.config.components.add("frontend")   # the panel needs the frontend; tests have none
    with patch("homeassistant.components.panel_custom.async_register_panel", new=AsyncMock()) as reg:
        entry = await _setup(hass, aioclient_mock, payload)
        assert not reg.called   # no features.panel in the payload
        assert await hass.config_entries.async_unload(entry.entry_id)

        payload["features"] = {"panel": True}
        aioclient_mock.clear_requests()
        aioclient_mock.get(API_URL, json=payload)
        with patch("homeassistant.components.frontend.async_remove_panel") as rem:
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()
            reg.assert_called_once()
            kw = reg.call_args.kwargs
            assert kw["frontend_url_path"] == "3dsearch" and kw["webcomponent_name"] == "threedsearch-panel"
            assert kw["require_admin"] is True and kw["config"] == {"entry_id": entry.entry_id}
            assert kw["module_url"].startswith("/3dsearch/3dsearch-panel.js?v=")
            assert await hass.config_entries.async_unload(entry.entry_id)
            rem.assert_called_once()


async def test_embed_sign_in(hass: HomeAssistant, aioclient_mock, payload, hass_ws_client, hass_read_only_access_token) -> None:
    payload["features"] = {"panel": True}
    entry = await _setup(hass, aioclient_mock, payload)

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "3dsearch/embed", "entry_id": entry.entry_id})
    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["token"] == EMBED["token"] and res["result"]["url"] == EMBED["url"]
    post = [c for c in aioclient_mock.mock_calls if c[0] == "POST"]
    assert post and post[-1][2] == {"cmd": "embed_token"}

    # Not for non-admin users: the sign-in can do everything the 3DSEARCH account can
    ro = await hass_ws_client(hass, hass_read_only_access_token)
    await ro.send_json_auto_id({"type": "3dsearch/embed", "entry_id": entry.entry_id})
    res = await ro.receive_json()
    assert not res["success"] and res["error"]["code"] == "unauthorized"

    await client.send_json_auto_id({"type": "3dsearch/embed", "entry_id": "nope"})
    res = await client.receive_json()
    assert not res["success"] and res["error"]["code"] == "not_found"


async def test_embed_refused_by_server(hass: HomeAssistant, aioclient_mock, payload, hass_ws_client) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="1", data={"api_key": KEY})
    entry.add_to_hass(hass)
    aioclient_mock.get(API_URL, json=payload)
    aioclient_mock.post(API_URL, json={"error": "not_allowed"}, status=403)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "3dsearch/embed", "entry_id": entry.entry_id})
    res = await client.receive_json()
    assert not res["success"] and res["error"] == {"code": "embed_failed", "message": "not_allowed"}
