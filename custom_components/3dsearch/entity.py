"""Base entities: one device for the account (spool stock) and one per printer."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SITE_URL
from .coordinator import ThreeDSearchCoordinator

_VIA_DEVICE_ID = "via_device_id" in DeviceInfo.__annotations__


def account_device(coordinator: ThreeDSearchCoordinator) -> DeviceInfo:
    """The 3DSEARCH account as a service device; printers hang below it."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"account_{coordinator.account_id}")},
        name="3DSEARCH",
        manufacturer="3DSEARCH",
        model="Printers & Filament",
        entry_type=DeviceEntryType.SERVICE,
        configuration_url=SITE_URL,
    )


class ThreeDSearchEntity(CoordinatorEntity[ThreeDSearchCoordinator]):
    """Entity on the account device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ThreeDSearchCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.account_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = account_device(coordinator)


class PrinterEntity(CoordinatorEntity[ThreeDSearchCoordinator]):
    """Entity on a printer device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ThreeDSearchCoordinator, printer_id: str, key: str) -> None:
        super().__init__(coordinator)
        self.printer_id = printer_id
        p = coordinator.printer(printer_id) or {}
        self._attr_unique_id = f"{coordinator.account_id}_{p.get('provider', 'printer')}_{printer_id}_{key}"
        self._attr_translation_key = key
        info = DeviceInfo(
            identifiers={(DOMAIN, f"{p.get('provider', 'printer')}_{printer_id}")},
            name=p.get("name") or printer_id,
            manufacturer=p.get("brand"),
            model=p.get("model"),
            sw_version=p.get("fw"),
            configuration_url=f"{SITE_URL}#printers",
        )
        # HA 2026.9 replaced via_device (identifier tuple) by via_device_id; older versions only know via_device
        if _VIA_DEVICE_ID and coordinator.account_device_id:
            info["via_device_id"] = coordinator.account_device_id
        else:
            info["via_device"] = (DOMAIN, f"account_{coordinator.account_id}")
        self._attr_device_info = info

    @property
    def printer(self) -> dict[str, Any]:
        """Latest printer data (empty when the printer disappeared)."""
        return self.coordinator.printer(self.printer_id) or {}

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.printer(self.printer_id) is not None

    @property
    def job(self) -> dict[str, Any]:
        """Running job or empty dict."""
        return self.printer.get("job") or {}


def add_spool_entities(entry, coordinator: ThreeDSearchCoordinator, async_add_entities, factory) -> None:
    """Create one entity per active spool now and for spools added later on 3dsearch.net."""
    known: set[str] = set()

    def _add() -> None:
        new = [factory(spool_id) for spool_id in (coordinator.data or {}).get("spool_items", {}) if spool_id not in known]
        known.update((coordinator.data or {}).get("spool_items", {}))
        if new:
            async_add_entities(new)

    _add()
    entry.async_on_unload(coordinator.async_add_listener(_add))


def add_printer_entities(entry, coordinator: ThreeDSearchCoordinator, async_add_entities, factory) -> None:
    """Create entities for every printer now and for printers/slots that show up later.

    ``factory(printer_id, printer)`` returns ``{key: entity}``; a key is only ever added once.
    """
    known: set[str] = set()

    def _add() -> None:
        new = []
        for printer_id, printer in (coordinator.data or {}).get("printers", {}).items():
            for key, entity in factory(printer_id, printer).items():
                if key not in known:
                    known.add(key)
                    new.append(entity)
        if new:
            async_add_entities(new)

    _add()
    entry.async_on_unload(coordinator.async_add_listener(_add))


class BoxEntity(PrinterEntity):
    """Entity of one filament box (ACE, AMS, CFS) of a printer — on the printer device."""

    def __init__(self, coordinator: ThreeDSearchCoordinator, printer_id: str, box: dict[str, Any], key: str) -> None:
        super().__init__(coordinator, printer_id, f"box{box['id']}_{key}")
        self.box_id = box["id"]
        self._attr_translation_key = f"box_{key}"
        self._attr_translation_placeholders = {"box": str(box.get("label") or f"Box {box['id'] + 1}")}

    @property
    def box(self) -> dict[str, Any]:
        """Latest data of this box (empty when it disappeared)."""
        return next((b for b in self.printer.get("boxes") or [] if b.get("id") == self.box_id), {})

    @property
    def available(self) -> bool:
        return super().available and bool(self.box)

    @property
    def box_attributes(self) -> dict[str, Any]:
        """Lets the dashboard card group the entities of one box."""
        return {"box_id": self.box_id, "box": self._attr_translation_placeholders["box"]}
