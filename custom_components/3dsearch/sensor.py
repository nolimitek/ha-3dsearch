"""Sensors: printer state, job progress, temperatures, slots and the spool stock."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfMass, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import STATES
from .coordinator import ThreeDSearchConfigEntry, ThreeDSearchCoordinator
from .entity import PrinterEntity, ThreeDSearchEntity, add_printer_entities, add_spool_entities


def _ts(value: str | None) -> datetime | None:
    return dt_util.parse_datetime(value) if value else None


@dataclass(frozen=True, kw_only=True)
class PrinterSensorDescription(SensorEntityDescription):
    """Sensor reading one value from the printer dict."""

    value: Callable[[dict[str, Any]], Any]


PRINTER_SENSORS: tuple[PrinterSensorDescription, ...] = (
    PrinterSensorDescription(
        key="status",
        device_class=SensorDeviceClass.ENUM,
        options=STATES,
        value=lambda p: p.get("state") if p.get("state") in STATES else None,
    ),
    PrinterSensorDescription(
        key="progress",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda p: (p.get("job") or {}).get("progress"),
    ),
    PrinterSensorDescription(
        key="remaining_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value=lambda p: (p.get("job") or {}).get("remain_min"),
    ),
    PrinterSensorDescription(
        key="end_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value=lambda p: _ts((p.get("job") or {}).get("end_at")),
    ),
    PrinterSensorDescription(
        key="job_name",
        value=lambda p: (p.get("job") or {}).get("title") or None,
    ),
    PrinterSensorDescription(
        key="current_layer",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda p: (p.get("job") or {}).get("layer"),
    ),
    PrinterSensorDescription(
        key="nozzle_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda p: p.get("nozzle"),
    ),
    PrinterSensorDescription(
        key="bed_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda p: p.get("bed"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ThreeDSearchConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    async_add_entities([SpoolCountSensor(coordinator), StockSensor(coordinator), LowSpoolsSensor(coordinator)])

    def factory(printer_id: str, printer: dict[str, Any]) -> dict[str, SensorEntity]:
        out: dict[str, SensorEntity] = {
            f"{printer_id}_{d.key}": PrinterSensor(coordinator, printer_id, d) for d in PRINTER_SENSORS
        }
        for slot in printer.get("slots") or []:
            out[f"{printer_id}_slot_{slot['index']}"] = SlotSensor(coordinator, printer_id, slot)
        return out

    add_printer_entities(entry, coordinator, async_add_entities, factory)
    add_spool_entities(entry, coordinator, async_add_entities, lambda spool_id: SpoolSensor(coordinator, spool_id))


class PrinterSensor(PrinterEntity, SensorEntity):
    """A value of one printer."""

    entity_description: PrinterSensorDescription

    def __init__(self, coordinator: ThreeDSearchCoordinator, printer_id: str, description: PrinterSensorDescription) -> None:
        super().__init__(coordinator, printer_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.printer)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        key = self.entity_description.key
        if key == "status":
            return {"error": self.printer.get("error"), "provider": self.printer.get("provider"),
                    "last_update": self.printer.get("updated")}
        if key == "current_layer":
            return {"total_layers": self.job.get("layers")}
        return None


class SlotSensor(PrinterEntity, SensorEntity):
    """One filament slot: remaining grams of the spool assigned on 3dsearch.net, material/colour as attributes."""

    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_native_unit_of_measurement = UnitOfMass.GRAMS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ThreeDSearchCoordinator, printer_id: str, slot: dict[str, Any]) -> None:
        super().__init__(coordinator, printer_id, f"slot_{slot['index']}")
        self.index = slot["index"]
        self._attr_translation_key = "slot"
        self._attr_translation_placeholders = {"slot": str(slot.get("label") or slot["index"] + 1)}

    @property
    def slot(self) -> dict[str, Any]:
        return next((s for s in self.printer.get("slots") or [] if s.get("index") == self.index), {})

    @property
    def available(self) -> bool:
        return super().available and bool(self.slot)

    @property
    def native_value(self) -> int | None:
        spool = self.slot.get("spool")
        return spool.get("left") if spool else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        slot = self.slot
        spool = slot.get("spool") or {}
        return {
            "slot": slot.get("label"),
            "index": slot.get("index"),
            "material": slot.get("material"),
            "color": slot.get("color"),
            "spool_id": spool.get("id"),
            "spool_name": spool.get("name"),
            "brand": spool.get("brand"),
            "remaining_percent": spool.get("pct"),
            "spool_weight": spool.get("total"),
        }


class SpoolCountSensor(ThreeDSearchEntity, SensorEntity):
    """Active spools in stock."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ThreeDSearchCoordinator) -> None:
        super().__init__(coordinator, "spools")

    @property
    def native_value(self) -> int | None:
        return (self.coordinator.data or {}).get("spools", {}).get("count")


class StockSensor(ThreeDSearchEntity, SensorEntity):
    """Filament left on all active spools."""

    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_native_unit_of_measurement = UnitOfMass.GRAMS
    _attr_suggested_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_suggested_display_precision = 1
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ThreeDSearchCoordinator) -> None:
        super().__init__(coordinator, "filament_stock")

    @property
    def native_value(self) -> int | None:
        return (self.coordinator.data or {}).get("spools", {}).get("left_g")


class LowSpoolsSensor(ThreeDSearchEntity, SensorEntity):
    """Spools that are almost empty (below the threshold of 3dsearch.net)."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ThreeDSearchCoordinator) -> None:
        super().__init__(coordinator, "low_spools")

    @property
    def native_value(self) -> int | None:
        low = (self.coordinator.data or {}).get("spools", {}).get("low")
        return len(low) if isinstance(low, list) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        spools = (self.coordinator.data or {}).get("spools", {})
        return {
            "threshold_g": spools.get("low_g"),
            "spools": [
                {"name": s.get("name"), "brand": s.get("brand"), "material": s.get("material"),
                 "color": s.get("color"), "left_g": s.get("left")}
                for s in spools.get("low") or []
            ],
        }


class SpoolSensor(ThreeDSearchEntity, SensorEntity):
    """One spool of the stock on 3dsearch.net: remaining grams; brand, material, colour, location as attributes."""

    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_native_unit_of_measurement = UnitOfMass.GRAMS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ThreeDSearchCoordinator, spool_id: str) -> None:
        super().__init__(coordinator, "spool")
        self.spool_id = spool_id
        self._attr_unique_id = f"{coordinator.account_id}_spool_{spool_id}"
        spool = coordinator.spool(spool_id) or {}
        self._attr_translation_placeholders = {"spool": spool.get("name") or f"#{spool_id}"}

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.spool(self.spool_id) is not None

    @property
    def native_value(self) -> int | None:
        return (self.coordinator.spool(self.spool_id) or {}).get("left")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        s = self.coordinator.spool(self.spool_id) or {}
        loaded = s.get("loaded") or {}
        return {
            "spool_id": s.get("id"),
            "spool_name": s.get("name"),
            "brand": s.get("brand"),
            "material": s.get("material"),
            "color": s.get("color"),
            "remaining_percent": s.get("pct"),
            "spool_weight": s.get("total"),
            "location": s.get("location"),
            "printer": loaded.get("printer"),
            "slot": loaded.get("slot"),
        }
