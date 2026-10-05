"""Config flow: valid key, wrong key, server down, duplicate account, reauth."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import API_URL, DOMAIN, KEY


async def test_user_flow_ok(hass: HomeAssistant, aioclient_mock, payload) -> None:
    aioclient_mock.get(API_URL, json=payload)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": f"  {KEY} "})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "3DSEARCH (Tester)"
    assert result["data"] == {"api_key": KEY}
    assert result["result"].unique_id == "1"
    assert aioclient_mock.mock_calls[0][3]["Authorization"] == f"Bearer {KEY}"


async def test_user_flow_errors(hass: HomeAssistant, aioclient_mock) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": "nonsense"})
    assert result["errors"] == {"api_key": "invalid_key"}

    aioclient_mock.get(API_URL, status=401, json={"error": "auth"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": KEY})
    assert result["errors"] == {"base": "invalid_key"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(API_URL, status=403, json={"error": "not_allowed"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": KEY})
    assert result["errors"] == {"base": "not_allowed"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(API_URL, status=502, text="Bad gateway")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": KEY})
    assert result["errors"] == {"base": "cannot_connect"}


async def test_already_configured(hass: HomeAssistant, aioclient_mock, payload) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id="1", data={"api_key": KEY}).add_to_hass(hass)
    aioclient_mock.get(API_URL, json=payload)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": KEY})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth(hass: HomeAssistant, aioclient_mock, payload) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="1", data={"api_key": "3ds_" + "00" * 20})
    entry.add_to_hass(hass)
    aioclient_mock.get(API_URL, json=payload)
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": KEY})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data["api_key"] == KEY


async def test_reauth_wrong_account(hass: HomeAssistant, aioclient_mock, payload) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="7", data={"api_key": KEY})
    entry.add_to_hass(hass)
    aioclient_mock.get(API_URL, json=payload)
    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"api_key": KEY})
    assert result["reason"] == "wrong_account"


async def test_options(hass: HomeAssistant, aioclient_mock, payload) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="1", data={"api_key": KEY})
    entry.add_to_hass(hass)
    aioclient_mock.get(API_URL, json=payload)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"scan_interval": 120})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"scan_interval": 120}
