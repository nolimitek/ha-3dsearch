"""Constants for the 3DSEARCH integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "3dsearch"
API_URL: Final = "https://3dsearch.net/api/ha.php"
SITE_URL: Final = "https://3dsearch.net/filament/"

CONF_API_KEY: Final = "api_key"
CONF_SCAN_INTERVAL: Final = "scan_interval"
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds; the server syncs printer clouds at most once a minute
MIN_SCAN_INTERVAL: Final = 30
MAX_SCAN_INTERVAL: Final = 600

# Printer states reported by the server (sensor "status")
STATES: Final = ["idle", "printing", "paused", "error", "offline"]
# Print events (event entity "print")
EVENT_STARTED: Final = "started"
EVENT_FINISHED: Final = "finished"
EVENT_FAILED: Final = "failed"
