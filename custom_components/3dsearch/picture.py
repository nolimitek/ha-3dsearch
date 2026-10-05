"""Spool pictures: a small SVG of a filament spool in the real colour, the winding shrinks with the remaining amount.

Used as entity_picture, so Home Assistant shows the spool instead of the generic weight icon in device pages,
entity lists, tile cards and the more-info dialog. Inline data URI — nothing to download, works offline.
"""

from __future__ import annotations

import base64
import re

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
RIM = "#5b6370"      # flanges and hub (readable on light and dark themes)
EMPTY = "#c7ccd4"    # visible flange where the filament is used up
HOLE = "#eef0f3"


def spool_svg(color: str | None, percent: float | None) -> str | None:
    """SVG markup, or None for an unknown colour (Home Assistant then keeps the icon)."""
    if not isinstance(color, str) or not _HEX.match(color):
        return None
    p = 100.0 if percent is None else max(0.0, min(100.0, float(percent)))
    hub, full = 7.5, 17.5
    r = hub + 2.0 + (full - hub - 2.0) * p / 100   # a ring of at least 2 units: the colour stays recognisable on almost empty spools
    lines = "".join(
        f"<circle cx='20' cy='20' r='{x:.1f}' fill='none' stroke='#000' stroke-opacity='.13' stroke-width='.6'/>"
        for x in [hub + 2.2 * i for i in range(1, 5)] if x < r - 0.8
    )
    filament = f"<circle cx='20' cy='20' r='{r:.1f}' fill='{color}'/>{lines}" if p > 0 else ""
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'>"
        f"<circle cx='20' cy='20' r='19.5' fill='{RIM}'/><circle cx='20' cy='20' r='{full}' fill='{EMPTY}'/>"
        f"{filament}"
        f"<circle cx='20' cy='20' r='{hub}' fill='{RIM}'/><circle cx='20' cy='20' r='3.2' fill='{HOLE}'/>"
        "</svg>"
    )


def spool_picture(color: str | None, percent: float | None) -> str | None:
    """entity_picture value (base64 data URI — safe inside the CSS url() the frontend uses)."""
    svg = spool_svg(color, percent)
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode() if svg else None
