"""Spool pictures: real colour, winding shrinks with the remaining amount, nothing for unknown colours."""

from __future__ import annotations

import importlib
import re

picture = importlib.import_module("custom_components.3dsearch.picture")


def _radius(svg: str, color: str) -> float:
    return float(re.search(rf"r='([\d.]+)' fill='{color}'", svg).group(1))


def test_spool_svg() -> None:
    full, half, empty = (picture.spool_svg("#1baf7a", p) for p in (100, 50, 0))
    assert _radius(full, "#1baf7a") > _radius(half, "#1baf7a")
    assert "#1baf7a" not in empty                                # nothing left → no winding
    assert picture.spool_svg("#1baf7a", None) == full            # unknown amount → drawn full
    for bad in (None, "", "red", "#12345", "#1234567", "#12345g", "'/><script>"):
        assert picture.spool_svg(bad, 50) is None
        assert picture.spool_picture(bad, 50) is None
    assert picture.spool_picture("#ABCDEF", 10).startswith("data:image/svg+xml;base64,")
