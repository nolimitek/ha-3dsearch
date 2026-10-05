"""Binary sensors: printer online, printing, problem."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ThreeDSearchConfigEntry, ThreeDSearchCoordinator
from .entity import PrinterEntity, add_printer_entities

BINARY_SENSORS: dict[str, BinarySensorDeviceClass] = {
    "online": BinarySensorDeviceClass.CONNECTIVITY,
    "printing": BinarySensorDeviceClass.RUNNING,
    "problem": BinarySensorDeviceClass.PROBLEM,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ThreeDSearchConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up binary sensors."""
    coordinator = entry.runtime_data

    def factory(printer_id: str, printer: dict[str, Any]) -> dict[str, BinarySensorEntity]:
        return {f"{printer_id}_{k}": PrinterBinarySensor(coordinator, printer_id, k, dc) for k, dc in BINARY_SENSORS.items()}

    add_printer_entities(entry, coordinator, async_add_entities, factory)


class PrinterBinarySensor(PrinterEntity, BinarySensorEntity):
    """Online / printing (also while paused) / problem (Klipper not ready)."""

    def __init__(self, coordinator: ThreeDSearchCoordinator, printer_id: str, key: str, device_class: BinarySensorDeviceClass) -> None:
        super().__init__(coordinator, printer_id, key)
        self.key = key
        self._attr_device_class = device_class

    @property
    def available(self) -> bool:
        # "online" must stay available, otherwise an offline printer could never show as disconnected
        return self.coordinator.last_update_success and self.coordinator.printer(self.printer_id) is not None

    @property
    def is_on(self) -> bool | None:
        state = self.printer.get("state")
        if self.key == "online":
            return bool(self.printer.get("online"))
        if self.key == "printing":
            return state in ("printing", "paused")
        return state == "error"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {"error": self.printer.get("error")} if self.key == "problem" else None
