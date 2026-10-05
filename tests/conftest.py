"""Shared fixtures: a realistic payload of https://3dsearch.net/api/ha.php."""

from __future__ import annotations

import copy
from typing import Any

import pytest

# Home Assistant mounts its test config dir (which has its own custom_components package) the first time it looks for
# custom integrations — importing ours first makes the loader find this repository's integration.
import custom_components  # noqa: F401

DOMAIN = "3dsearch"
API_URL = "https://3dsearch.net/api/ha.php"
KEY = "3ds_" + "a1" * 20

PAYLOAD: dict[str, Any] = {
    "v": 1,
    "account": {"id": 1, "name": "Tester"},
    "printers": [
        {
            "id": "a3c12bb1ca4ea642", "provider": "moonraker", "brand": "Klipper", "name": "Printsaurus",
            "model": "Anycubic Kobra S1", "fw": "Rinkhals 20260716_02", "online": True, "state": "printing", "error": None,
            "nozzle": 220, "bed": 60,
            "job": {"title": "Benchy", "progress": 42, "remain_min": 37, "end_at": "2026-10-05T13:00:00Z", "layer": 80, "layers": 240},
            "slots": [
                {"index": 0, "label": "1", "material": "PLA", "color": "#0047bb",
                 "spool": {"id": 31, "name": "PLA Blue", "brand": "Sunlu", "material": "PLA", "color": "#0047bb",
                           "left": 358, "total": 1000, "pct": 36, "value": 5.33}},
                {"index": 1, "label": "2", "material": "PETG", "color": "#f40031", "spool": None},
            ],
            "boxes": [{"id": 0, "label": "ACE 1", "control": True, "temp": 31, "humidity": None, "drying": False,
                       "dry_target": None, "dry_remain_min": None, "dry_duration_min": None}],
            "control": True,
            "last_job": {"id": 100, "title": "Benchy", "status": "printing", "start": "2026-10-05T12:00:00Z", "end": None, "grams": None},
            "updated": "2026-10-05T12:20:00Z",
        },
        {
            "id": "01P00A123", "provider": "bambu", "brand": "Bambu Lab", "name": "X1C", "model": "X1 Carbon", "fw": "01.08",
            "online": False, "state": "offline", "error": None, "nozzle": None, "bed": None, "job": None,
            "slots": [], "control": False, "last_job": None, "updated": "2026-10-05T12:19:00Z",
            "boxes": [{"id": 0, "label": "AMS 1", "control": False, "temp": 52, "humidity": 18, "drying": True,
                       "dry_target": 65, "dry_remain_min": 128, "dry_duration_min": None}],
        },
    ],
    "spools": {"count": 28, "left_g": 16570, "value": 233.32, "low_g": 150,
               "low": [{"id": 9, "name": "Black PLA", "brand": None, "material": "PLA", "color": "#000000", "left": 80}],
               "items": [
                   {"id": 31, "name": "PLA Blue", "brand": "Sunlu", "material": "PLA", "color": "#0047bb", "left": 358, "total": 1000,
                    "pct": 36, "value": 5.33, "location": "ACE Pro", "loaded": {"printer": "Printsaurus", "slot": "1"}},
                   {"id": 9, "name": "Black PLA", "brand": None, "material": "PLA", "color": "#000000", "left": 80, "total": 1000,
                    "pct": 8, "value": None, "location": "Shelf", "loaded": None},
               ]},
    "time": "2026-10-05T12:20:00Z",
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/ in every test."""
    yield


@pytest.fixture
def payload() -> dict[str, Any]:
    return copy.deepcopy(PAYLOAD)
