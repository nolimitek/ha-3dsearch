"""Drying settings per ACE (temperature, duration) — used when the drying switch is turned on. Kept in Home Assistant."""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DRY_HOURS_DEFAULT, DRY_HOURS_MAX, DRY_HOURS_MIN, DRY_TEMP_DEFAULT, DRY_TEMP_MAX, DRY_TEMP_MIN
from .coordinator import ThreeDSearchConfigEntry, ThreeDSearchCoordinator
from .entity import BoxEntity, add_printer_entities

SETTINGS = {
    "dry_temperature": (DRY_TEMP_MIN, DRY_TEMP_MAX, 1, DRY_TEMP_DEFAULT, UnitOfTemperature.CELSIUS),
    "dry_duration": (DRY_HOURS_MIN, DRY_HOURS_MAX, 1, DRY_HOURS_DEFAULT, UnitOfTime.HOURS),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ThreeDSearchConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up drying settings for boxes 3dsearch.net can dry."""
    coordinator = entry.runtime_data

    def factory(printer_id: str, printer: dict[str, Any]) -> dict[str, RestoreNumber]:
        return {
            f"{printer_id}_box{box['id']}_{key}": DryingSetting(coordinator, printer_id, box, key)
            for box in printer.get("boxes") or [] if box.get("control") for key in SETTINGS
        }

    add_printer_entities(entry, coordinator, async_add_entities, factory)


class DryingSetting(BoxEntity, RestoreNumber):
    """Temperature (°C) or duration (h) for the next drying run of this box."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: ThreeDSearchCoordinator, printer_id: str, box: dict[str, Any], key: str) -> None:
        super().__init__(coordinator, printer_id, box, key)
        lo, hi, step, default, unit = SETTINGS[key]
        self._attr_native_min_value, self._attr_native_max_value, self._attr_native_step = lo, hi, step
        self._attr_native_unit_of_measurement = unit
        self._attr_native_value = default

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) and last.native_value is not None:
            self._attr_native_value = last.native_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.box_attributes

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
