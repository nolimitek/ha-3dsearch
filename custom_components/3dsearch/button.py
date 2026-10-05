"""Buttons: pause, resume and cancel the running print (Anycubic Cloud and Klipper agent printers)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import ThreeDSearchError
from .const import DOMAIN
from .coordinator import ThreeDSearchConfigEntry, ThreeDSearchCoordinator
from .entity import PrinterEntity, add_printer_entities

# key → (server command, printer states in which the button makes sense)
BUTTONS: dict[str, tuple[str, tuple[str, ...]]] = {
    "pause": ("pause", ("printing",)),
    "resume": ("resume", ("paused",)),
    "cancel": ("stop", ("printing", "paused")),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ThreeDSearchConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up buttons for printers 3dsearch.net can control (Bambu Lab, Creality and Elegoo are read-only)."""
    coordinator = entry.runtime_data

    def factory(printer_id: str, printer: dict[str, Any]) -> dict[str, ButtonEntity]:
        if not printer.get("control"):
            return {}
        return {f"{printer_id}_{k}": PrinterButton(coordinator, printer_id, k) for k in BUTTONS}

    add_printer_entities(entry, coordinator, async_add_entities, factory)


class PrinterButton(PrinterEntity, ButtonEntity):
    """Only available while it makes sense: pause while printing, resume while paused."""

    def __init__(self, coordinator: ThreeDSearchCoordinator, printer_id: str, key: str) -> None:
        super().__init__(coordinator, printer_id, key)
        self.cmd, self.states = BUTTONS[key]

    @property
    def available(self) -> bool:
        return super().available and self.printer.get("state") in self.states

    async def async_press(self) -> None:
        try:
            await self.coordinator.api.command(self.printer_id, self.cmd)
        except ThreeDSearchError as err:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="command_failed",
                                     translation_placeholders={"error": err.code}) from err
        await self.coordinator.async_request_refresh()
