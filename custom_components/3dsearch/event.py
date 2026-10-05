"""Event entity per printer: print started / finished / failed — for automations."""

from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import EVENT_FAILED, EVENT_FINISHED, EVENT_STARTED
from .coordinator import ThreeDSearchConfigEntry, ThreeDSearchCoordinator
from .entity import PrinterEntity, add_printer_entities


async def async_setup_entry(
    hass: HomeAssistant, entry: ThreeDSearchConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Set up event entities."""
    coordinator = entry.runtime_data

    def factory(printer_id: str, printer: dict[str, Any]) -> dict[str, EventEntity]:
        return {f"{printer_id}_print": PrintEvent(coordinator, printer_id)}

    add_printer_entities(entry, coordinator, async_add_entities, factory)


class PrintEvent(PrinterEntity, EventEntity):
    """Fires when the server's last job of this printer starts or ends.

    Based on the job history of 3dsearch.net (not on state changes seen by Home Assistant), so a print that
    ended while Home Assistant was restarting is still reported once. Nothing fires for the job that was
    already known when the integration started.
    """

    _attr_event_types = [EVENT_STARTED, EVENT_FINISHED, EVENT_FAILED]

    def __init__(self, coordinator: ThreeDSearchCoordinator, printer_id: str) -> None:
        super().__init__(coordinator, printer_id, "print")
        self._seen = self._key(self.printer.get("last_job"))

    @staticmethod
    def _key(job: dict[str, Any] | None) -> tuple[Any, Any] | None:
        return (job.get("id"), job.get("status")) if job else None

    @callback
    def _handle_coordinator_update(self) -> None:
        job = self.printer.get("last_job")
        key = self._key(job)
        if job and key != self._seen:
            new_job = self._seen is None or key[0] != self._seen[0]
            event = {"printing": EVENT_STARTED, "finished": EVENT_FINISHED, "failed": EVENT_FAILED}.get(job.get("status"))
            # A new job that is already over (short print between two polls) only reports its end
            if event and (event != EVENT_STARTED or new_job):
                self._trigger_event(event, {"job_name": job.get("title"), "start": job.get("start"),
                                            "end": job.get("end"), "filament_g": job.get("grams")})
        self._seen = key
        super()._handle_coordinator_update()
