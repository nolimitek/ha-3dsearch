"""Small client for the 3DSEARCH Home Assistant endpoint (https://3dsearch.net/api/ha.php)."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import API_URL

TIMEOUT = aiohttp.ClientTimeout(total=60)


class ThreeDSearchError(Exception):
    """Generic error talking to 3DSEARCH."""

    def __init__(self, code: str = "unknown") -> None:
        super().__init__(code)
        self.code = code


class ThreeDSearchAuthError(ThreeDSearchError):
    """The API key is invalid or was revoked."""


class ThreeDSearchApi:
    """Read the printer/spool state and send print commands with a personal API key."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str, url: str = API_URL) -> None:
        self._session = session
        self._key = api_key.strip()
        self._url = url

    async def _request(self, method: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            async with self._session.request(
                method,
                self._url,
                json=json,
                headers={"Authorization": f"Bearer {self._key}", "Accept": "application/json"},
                timeout=TIMEOUT,
            ) as resp:
                try:
                    data = await resp.json(content_type=None)
                except ValueError:
                    data = None
                if resp.status in (401, 403):
                    raise ThreeDSearchAuthError((data or {}).get("error", "auth"))
                if resp.status >= 400 or not isinstance(data, dict):
                    raise ThreeDSearchError((data or {}).get("error", f"http_{resp.status}") if isinstance(data, dict) else f"http_{resp.status}")
                return data
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise ThreeDSearchError("connection") from err

    async def status(self) -> dict[str, Any]:
        """Return printers, slots and spool stock in one call."""
        return await self._request("GET")

    async def command(self, printer_id: str, cmd: str, **params: Any) -> None:
        """Pause/resume/stop a print or start/stop drying (Anycubic Cloud and Klipper agent printers only)."""
        await self._request("POST", {"printer": printer_id, "cmd": cmd, **params})
