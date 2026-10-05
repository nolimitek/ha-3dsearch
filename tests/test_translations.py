"""Every language file has exactly the keys of strings.json."""

from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).parent.parent / "custom_components" / "3dsearch"


def _keys(node, prefix=""):
    if isinstance(node, dict):
        out = set()
        for k, v in node.items():
            out |= _keys(v, f"{prefix}.{k}")
        return out
    return {prefix}


def test_translations_complete() -> None:
    reference = _keys(json.loads((BASE / "strings.json").read_text(encoding="utf-8")))
    files = sorted((BASE / "translations").glob("*.json"))
    assert {f.stem for f in files} == {"de", "en", "es", "fr", "it", "nl"}
    for f in files:
        keys = _keys(json.loads(f.read_text(encoding="utf-8")))
        assert keys == reference, (f.name, keys ^ reference)
