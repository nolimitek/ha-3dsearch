"""Counters, maintenance, filament printed, costs of the month and spools to dry (0.5.0b6)."""

from __future__ import annotations

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import API_URL, DOMAIN, KEY


async def _setup(hass: HomeAssistant, aioclient_mock, payload) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="1", data={"api_key": KEY})
    entry.add_to_hass(hass)
    aioclient_mock.get(API_URL, json=payload)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_counters_only_where_reported(hass: HomeAssistant, aioclient_mock, payload) -> None:
    await _setup(hass, aioclient_mock, payload)
    prints = hass.states.get("sensor.printsaurus_total_prints")
    assert prints.state == "98" and prints.attributes["state_class"] == "total_increasing"
    hours = hass.states.get("sensor.printsaurus_total_print_time")
    assert float(hours.state) == 359 and hours.attributes["unit_of_measurement"] == "h"
    fil = hass.states.get("sensor.printsaurus_total_filament")
    assert float(fil.state) == 2850 and fil.attributes["unit_of_measurement"] == "m"
    # The Bambu printer reports no counters → no empty sensors for it
    assert hass.states.get("sensor.x1c_total_prints") is None
    assert hass.states.get("sensor.x1c_total_filament") is None


async def test_maintenance(hass: HomeAssistant, aioclient_mock, payload) -> None:
    entry = await _setup(hass, aioclient_mock, payload)
    nxt = hass.states.get("sensor.printsaurus_next_maintenance")
    assert nxt.state == "104" and nxt.attributes["task"] == "Clean the nozzle"
    assert nxt.attributes["remaining"] == -2.1 and nxt.attributes["unit"] == "h" and len(nxt.attributes["tasks"]) == 2
    due = hass.states.get("binary_sensor.printsaurus_maintenance_due")
    assert due.state == "on" and due.attributes["tasks"] == ["Clean the nozzle"]
    assert hass.states.get("binary_sensor.x1c_maintenance_due") is None   # no plan for it

    # Task done on 3dsearch.net → not due any more
    m = payload["printers"][0]["maint"]
    m["due"] = False
    m["next"] = m["tasks"][0] = {"title": "Lubricate the rails", "state": "ok", "pct": 6, "by": "days", "remaining": 85, "unit": "d"}
    m["tasks"] = m["tasks"][:1]
    aioclient_mock.clear_requests()
    aioclient_mock.get(API_URL, json=payload)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.printsaurus_maintenance_due").state == "off"
    assert hass.states.get("sensor.printsaurus_next_maintenance").state == "6"


async def test_maintenance_plan_added_later(hass: HomeAssistant, aioclient_mock, payload) -> None:
    payload["printers"][0].pop("maint")
    entry = await _setup(hass, aioclient_mock, payload)
    assert hass.states.get("sensor.printsaurus_next_maintenance") is None
    payload["printers"][0]["maint"] = {"due": False, "next": {"title": "Check belts", "state": "soon", "pct": 90, "by": "prints",
                                                              "remaining": 3, "unit": "prints"},
                                       "tasks": [{"title": "Check belts", "state": "soon", "pct": 90, "by": "prints", "remaining": 3, "unit": "prints"}]}
    aioclient_mock.clear_requests()
    aioclient_mock.get(API_URL, json=payload)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.printsaurus_next_maintenance").state == "90"
    assert hass.states.get("binary_sensor.printsaurus_maintenance_due").state == "off"


async def test_usage_and_costs(hass: HomeAssistant, aioclient_mock, payload) -> None:
    await _setup(hass, aioclient_mock, payload)
    printed = hass.states.get("sensor.3dsearch_filament_printed")
    assert float(printed.state) == 12.623 and printed.attributes["unit_of_measurement"] == "kg"   # suggested unit
    assert printed.attributes["state_class"] == "total" and printed.attributes["prints"] == 140
    cost = hass.states.get("sensor.3dsearch_print_costs_this_month")
    assert float(cost.state) == 15.53 and cost.attributes["unit_of_measurement"] == "EUR"
    assert cost.attributes["state_class"] == "total" and cost.attributes["device_class"] == "monetary"
    assert cost.attributes["filament"] == 13.13 and cost.attributes["operating"] == 2.4

    dry = hass.states.get("sensor.3dsearch_spools_to_dry")
    assert dry.state == "1" and dry.attributes["spools"][0] == {"name": "TPU Red", "brand": "Sunlu", "material": "TPU",
                                                                "days": 21, "limit_days": 14}
    spool = hass.states.get("sensor.3dsearch_pla_blue")
    assert spool.attributes["dry_due"] is False and spool.attributes["days_open"] == 9


async def test_old_server_without_new_fields(hass: HomeAssistant, aioclient_mock, payload) -> None:
    """A server without usage/dry data must not break anything — the new sensors just stay unknown."""
    payload.pop("usage")
    payload["spools"].pop("dry_due")
    for p in payload["printers"]:
        p.pop("counters", None)
        p.pop("maint", None)
    await _setup(hass, aioclient_mock, payload)
    assert hass.states.get("sensor.3dsearch_filament_printed").state == STATE_UNKNOWN
    assert hass.states.get("sensor.3dsearch_print_costs_this_month").state == STATE_UNKNOWN
    assert hass.states.get("sensor.3dsearch_spools_to_dry").state == STATE_UNKNOWN
    assert hass.states.get("sensor.printsaurus_total_prints") is None
    assert hass.states.get("sensor.printsaurus_status").state != STATE_UNAVAILABLE
