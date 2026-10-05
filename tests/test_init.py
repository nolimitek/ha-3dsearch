"""Setup, entities, print events, buttons, revoked keys and printers added later."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
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


async def _refresh(hass: HomeAssistant, entry, aioclient_mock, payload=None, status=200) -> None:
    aioclient_mock.clear_requests()
    aioclient_mock.get(API_URL, json=payload if payload is not None else {"error": "auth"}, status=status)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


async def test_entities(hass: HomeAssistant, aioclient_mock, payload) -> None:
    entry = await _setup(hass, aioclient_mock, payload)
    assert entry.state is ConfigEntryState.LOADED

    assert hass.states.get("sensor.printsaurus_status").state == "printing"
    assert hass.states.get("sensor.printsaurus_progress").state == "42"
    assert hass.states.get("sensor.printsaurus_remaining_time").state == "37"
    assert hass.states.get("sensor.printsaurus_estimated_end").state == "2026-10-05T13:00:00+00:00"
    assert hass.states.get("sensor.printsaurus_job").state == "Benchy"
    layer = hass.states.get("sensor.printsaurus_current_layer")
    assert layer.state == "80" and layer.attributes["total_layers"] == 240
    assert hass.states.get("sensor.printsaurus_nozzle_temperature").state == "220"
    assert hass.states.get("sensor.printsaurus_bed_temperature").state == "60"

    slot1 = hass.states.get("sensor.printsaurus_slot_1")
    assert slot1.state == "358"
    assert slot1.attributes["material"] == "PLA" and slot1.attributes["spool_name"] == "PLA Blue"
    assert hass.states.get("sensor.printsaurus_slot_2").state == STATE_UNKNOWN   # no spool assigned

    assert hass.states.get("binary_sensor.printsaurus_online").state == "on"
    assert hass.states.get("binary_sensor.printsaurus_printing").state == "on"
    assert hass.states.get("binary_sensor.printsaurus_problem").state == "off"

    assert hass.states.get("button.printsaurus_pause_print").state != STATE_UNAVAILABLE
    assert hass.states.get("button.printsaurus_resume_print").state == STATE_UNAVAILABLE   # not paused
    assert hass.states.get("button.printsaurus_cancel_print").state != STATE_UNAVAILABLE

    # Bambu Lab: read-only, offline
    assert hass.states.get("sensor.x1c_status").state == "offline"
    assert hass.states.get("binary_sensor.x1c_online").state == "off"
    assert hass.states.get("button.x1c_pause_print") is None

    # Account device
    assert hass.states.get("sensor.3dsearch_spools_in_stock").state == "28"
    stock = hass.states.get("sensor.3dsearch_filament_in_stock")
    assert float(stock.state) == 16.57 and stock.attributes["unit_of_measurement"] == "kg"
    low = hass.states.get("sensor.3dsearch_spools_almost_empty")
    assert low.state == "1" and low.attributes["spools"][0]["left_g"] == 80

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_print_events(hass: HomeAssistant, aioclient_mock, payload) -> None:
    entry = await _setup(hass, aioclient_mock, payload)
    ev = "event.printsaurus_print"
    assert hass.states.get(ev).state == STATE_UNKNOWN   # the job known at start-up fires nothing

    payload["printers"][0]["last_job"].update(status="finished", end="2026-10-05T13:01:00Z", grams=11.3)
    payload["printers"][0].update(state="idle", job=None)
    await _refresh(hass, entry, aioclient_mock, payload)
    st = hass.states.get(ev)
    assert st.attributes["event_type"] == "finished"
    assert st.attributes["job_name"] == "Benchy" and st.attributes["filament_g"] == 11.3
    assert hass.states.get("sensor.printsaurus_progress").state == STATE_UNKNOWN
    assert hass.states.get("button.printsaurus_pause_print").state == STATE_UNAVAILABLE

    # Same data again: no second event
    first = st.state
    await _refresh(hass, entry, aioclient_mock, payload)
    assert hass.states.get(ev).state == first

    # Next job starts …
    payload["printers"][0]["last_job"] = {"id": 101, "title": "Cube", "status": "printing", "start": "2026-10-05T14:00:00Z", "end": None, "grams": None}
    await _refresh(hass, entry, aioclient_mock, payload)
    assert hass.states.get(ev).attributes["event_type"] == "started"
    # … and fails
    payload["printers"][0]["last_job"].update(status="failed", end="2026-10-05T14:03:00Z")
    await _refresh(hass, entry, aioclient_mock, payload)
    assert hass.states.get(ev).attributes["event_type"] == "failed"
    # A short job that started and ended between two polls only reports its end
    payload["printers"][0]["last_job"] = {"id": 102, "title": "Clip", "status": "finished", "start": "x", "end": "y", "grams": 1.0}
    await _refresh(hass, entry, aioclient_mock, payload)
    assert hass.states.get(ev).attributes["event_type"] == "finished"


async def test_buttons(hass: HomeAssistant, aioclient_mock, payload) -> None:
    await _setup(hass, aioclient_mock, payload)
    aioclient_mock.post(API_URL, json={"ok": True})
    await hass.services.async_call("button", "press", {"entity_id": "button.printsaurus_pause_print"}, blocking=True)
    post = [c for c in aioclient_mock.mock_calls if c[0] == "POST"]
    assert post[0][2] == {"printer": "a3c12bb1ca4ea642", "cmd": "pause"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(API_URL, json=payload)
    aioclient_mock.post(API_URL, status=400, json={"error": "too_fast"})
    try:
        await hass.services.async_call("button", "press", {"entity_id": "button.printsaurus_cancel_print"}, blocking=True)
    except Exception as err:   # HomeAssistantError with translated message
        assert "too_fast" in str(err) or getattr(err, "translation_placeholders", {}).get("error") == "too_fast"
    else:
        raise AssertionError("expected an error")


async def test_revoked_key_starts_reauth(hass: HomeAssistant, aioclient_mock, payload) -> None:
    entry = await _setup(hass, aioclient_mock, payload)
    await _refresh(hass, entry, aioclient_mock, None, status=401)
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert flows and flows[0]["context"]["source"] == "reauth"


async def test_server_down_marks_unavailable(hass: HomeAssistant, aioclient_mock, payload) -> None:
    entry = await _setup(hass, aioclient_mock, payload)
    await _refresh(hass, entry, aioclient_mock, {"error": "x"}, status=502)
    assert hass.states.get("sensor.printsaurus_status").state == STATE_UNAVAILABLE
    await _refresh(hass, entry, aioclient_mock, payload)
    assert hass.states.get("sensor.printsaurus_status").state == "printing"


async def test_new_printer_and_slot(hass: HomeAssistant, aioclient_mock, payload) -> None:
    entry = await _setup(hass, aioclient_mock, payload)
    payload["printers"][0]["slots"].append({"index": 2, "label": "3", "material": "TPU", "color": None, "spool": None})
    payload["printers"].append({**payload["printers"][1], "id": "K1", "provider": "creality", "brand": "Creality", "name": "K1 Max",
                                "online": True, "state": "idle"})
    await _refresh(hass, entry, aioclient_mock, payload)
    assert hass.states.get("sensor.printsaurus_slot_3") is not None
    assert hass.states.get("sensor.k1_max_status").state == "idle"

    # Printer removed on 3dsearch.net → its entities become unavailable
    payload["printers"] = payload["printers"][:1]
    await _refresh(hass, entry, aioclient_mock, payload)
    assert hass.states.get("sensor.k1_max_status").state == STATE_UNAVAILABLE


async def test_printer_hangs_below_account(hass: HomeAssistant, aioclient_mock, payload, caplog) -> None:
    from homeassistant.helpers import device_registry as dr

    entry = await _setup(hass, aioclient_mock, payload)
    reg = dr.async_get(hass)
    get = getattr(reg, "async_get_device_by_identifier", None)   # HA 2026.10+, async_get_device is deprecated there
    account = get((DOMAIN, "account_1"), entry.entry_id) if get else reg.async_get_device(identifiers={(DOMAIN, "account_1")})
    printer = (get((DOMAIN, "moonraker_a3c12bb1ca4ea642"), entry.entry_id) if get
               else reg.async_get_device(identifiers={(DOMAIN, "moonraker_a3c12bb1ca4ea642")}))
    assert account and printer and printer.via_device_id == account.id
    assert "deprecated `via_device`" not in caplog.text


async def test_setup_fails_with_bad_key(hass: HomeAssistant, aioclient_mock) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="1", data={"api_key": KEY})
    entry.add_to_hass(hass)
    aioclient_mock.get(API_URL, status=401, json={"error": "auth"})
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
