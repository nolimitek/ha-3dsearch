"""Sensors: printer state, job progress, temperatures, slots, counters, maintenance, the spool stock and usage."""

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
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfMass, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import STATES
from .coordinator import ThreeDSearchConfigEntry, ThreeDSearchCoordinator
from .entity import BoxEntity, PrinterEntity, ThreeDSearchEntity, add_printer_entities, add_spool_entities
from .picture import spool_picture


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


# Lifetime counters the printer reports itself (Anycubic, Klipper) — the numbers on top of the printer card on 3dsearch.net.
# total_increasing: a printer whose history is cleared starts again at 0, which Home Assistant's statistics handle as a reset.
COUNTER_SENSORS: tuple[PrinterSensorDescription, ...] = (
    PrinterSensorDescription(
        key="total_prints",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value=lambda p: (p.get("counters") or {}).get("prints"),
    ),
    PrinterSensorDescription(
        key="total_print_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value=lambda p: (p.get("counters") or {}).get("hours"),
    ),
    PrinterSensorDescription(
        key="total_filament",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value=lambda p: (p.get("counters") or {}).get("filament_m"),
    ),
)
COUNTER_FIELDS = {"total_prints": "prints", "total_print_time": "hours", "total_filament": "filament_m"}


async def async_setup_entry(
    hass: HomeAssistant, entry: ThreeDSearchConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    async_add_entities([SpoolCountSensor(coordinator), StockSensor(coordinator), LowSpoolsSensor(coordinator),
                        FilamentPrintedSensor(coordinator), MonthCostSensor(coordinator), SpoolsToDrySensor(coordinator)])

    def factory(printer_id: str, printer: dict[str, Any]) -> dict[str, SensorEntity]:
        out: dict[str, SensorEntity] = {
            f"{printer_id}_{d.key}": PrinterSensor(coordinator, printer_id, d) for d in PRINTER_SENSORS
        }
        # Counters and maintenance only where there is something: printers that report counters / have a maintenance plan
        counters = printer.get("counters") or {}
        for d in COUNTER_SENSORS:
            if counters.get(COUNTER_FIELDS[d.key]) is not None:
                out[f"{printer_id}_{d.key}"] = PrinterSensor(coordinator, printer_id, d)
        if printer.get("maint"):
            out[f"{printer_id}_maintenance"] = MaintenanceSensor(coordinator, printer_id)
        for slot in printer.get("slots") or []:
            out[f"{printer_id}_slot_{slot['index']}"] = SlotSensor(coordinator, printer_id, slot)
        for box in printer.get("boxes") or []:
            # Climate sensors only once the box reports a value (the ACE Pro has no humidity sensor)
            if box.get("temp") is not None:
                out[f"{printer_id}_box{box['id']}_temperature"] = BoxSensor(coordinator, printer_id, box, "temperature")
            if box.get("humidity") is not None:
                out[f"{printer_id}_box{box['id']}_humidity"] = BoxSensor(coordinator, printer_id, box, "humidity")
            out[f"{printer_id}_box{box['id']}_dry_remaining"] = BoxSensor(coordinator, printer_id, box, "dry_remaining")
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


class MaintenanceSensor(PrinterEntity, SensorEntity):
    """Maintenance plan of a printer: how far the next task is (100 % = due), the task and what is left as attributes."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ThreeDSearchCoordinator, printer_id: str) -> None:
        super().__init__(coordinator, printer_id, "maintenance")

    @property
    def maint(self) -> dict[str, Any]:
        return self.printer.get("maint") or {}

    @property
    def native_value(self) -> int | None:
        return (self.maint.get("next") or {}).get("pct")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        nxt = self.maint.get("next") or {}
        return {
            "task": nxt.get("title"),
            "state": nxt.get("state"),
            "remaining": nxt.get("remaining"),
            "unit": nxt.get("unit"),
            "tasks": self.maint.get("tasks") or [],
        }


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
    def entity_picture(self) -> str | None:
        spool = self.slot.get("spool") or {}
        return spool_picture(self.slot.get("color") or spool.get("color"), spool.get("pct"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        slot = self.slot
        spool = slot.get("spool") or {}
        return {
            "slot": slot.get("label"),
            "index": slot.get("index"),
            "material": slot.get("material"),
            "color": slot.get("color"),
            "in_use": bool(slot.get("in_use")),
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


class FilamentPrintedSensor(ThreeDSearchEntity, SensorEntity):
    """All filament that 3dsearch.net booked for finished and cancelled prints — for long-term statistics.

    state_class total, not total_increasing: a corrected booking on 3dsearch.net can lower the sum a little, and
    Home Assistant would read any drop of a total_increasing sensor as a meter reset.
    """

    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_native_unit_of_measurement = UnitOfMass.GRAMS
    _attr_suggested_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_suggested_display_precision = 2
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator: ThreeDSearchCoordinator) -> None:
        super().__init__(coordinator, "filament_printed")

    @property
    def usage(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("usage") or {}

    @property
    def native_value(self) -> int | None:
        return self.usage.get("filament_g")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"prints": self.usage.get("prints")}


class MonthCostSensor(ThreeDSearchEntity, SensorEntity):
    """Print costs of the current calendar month: filament plus electricity and wear (when set on 3dsearch.net)."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_suggested_display_precision = 2
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator: ThreeDSearchCoordinator) -> None:
        super().__init__(coordinator, "month_cost")

    @property
    def month(self) -> dict[str, Any]:
        return ((self.coordinator.data or {}).get("usage") or {}).get("month") or {}

    @property
    def native_unit_of_measurement(self) -> str:
        return self.month.get("currency") or "EUR"

    @property
    def native_value(self) -> float | None:
        return self.month.get("cost")

    @property
    def last_reset(self) -> datetime | None:
        return _ts(self.month.get("start"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        m = self.month
        return {"filament": m.get("material"), "operating": m.get("run"), "prints": m.get("prints"), "grams": m.get("grams")}


class SpoolsToDrySensor(ThreeDSearchEntity, SensorEntity):
    """Open spools that should be dried (days since opening/drying, limit by material — as in the spool list)."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ThreeDSearchCoordinator) -> None:
        super().__init__(coordinator, "spools_to_dry")

    @property
    def native_value(self) -> int | None:
        due = (self.coordinator.data or {}).get("spools", {}).get("dry_due")
        return len(due) if isinstance(due, list) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "spools": [
                {"name": s.get("name"), "brand": s.get("brand"), "material": s.get("material"),
                 "days": s.get("days"), "limit_days": s.get("limit")}
                for s in (self.coordinator.data or {}).get("spools", {}).get("dry_due") or []
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
    def entity_picture(self) -> str | None:
        spool = self.coordinator.spool(self.spool_id) or {}
        return spool_picture(spool.get("color"), spool.get("pct"))

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
            "dry_due": bool((s.get("dry") or {}).get("due")),
            "days_open": (s.get("dry") or {}).get("days"),
        }


class BoxSensor(BoxEntity, SensorEntity):
    """Temperature / humidity inside a box, remaining drying time."""

    def __init__(self, coordinator: ThreeDSearchCoordinator, printer_id: str, box: dict[str, Any], key: str) -> None:
        super().__init__(coordinator, printer_id, box, key)
        self.key = key
        if key == "temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key == "humidity":
            self._attr_device_class = SensorDeviceClass.HUMIDITY
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_native_unit_of_measurement = UnitOfTime.MINUTES

    @property
    def native_value(self) -> int | None:
        box = self.box
        if self.key == "temperature":
            return box.get("temp")
        if self.key == "humidity":
            return box.get("humidity")
        return box.get("dry_remain_min") if box.get("drying") else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self.key != "dry_remaining":
            return self.box_attributes
        box = self.box
        return {**self.box_attributes, "drying": bool(box.get("drying")), "target_temperature": box.get("dry_target"),
                "duration": box.get("dry_duration_min"), "controllable": bool(box.get("control"))}
