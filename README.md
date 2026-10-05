# 3DSEARCH Printers & Filament for Home Assistant

Brings your printers and filament stock from [3dsearch.net](https://3dsearch.net/filament/) into Home Assistant:
**Anycubic Cloud, Bambu Lab, Creality Cloud, Elegoo and Klipper** in one integration, together with the spools you manage on 3dsearch.net.

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=nolimitek&repository=ha-3dsearch&category=integration)

## What you get

Per printer (one device each):

| Entity | |
|---|---|
| `sensor` Status | idle / printing / paused / error / offline |
| `sensor` Progress, Remaining time, Estimated end, Job, Current layer | while printing |
| `sensor` Nozzle / Bed temperature | |
| `sensor` Slot 1…n | remaining grams of the spool in that slot; material, colour, brand as attributes |
| `binary_sensor` Online, Printing, Problem | Problem = Klipper not ready (with the error message) |
| `button` Pause / Resume / Cancel print | Anycubic Cloud and Klipper only — Bambu Lab, Creality and Elegoo are read-only |
| `event` Print | `started`, `finished`, `failed` — for automations |

For the account: **Spools in stock**, **Filament in stock**, **Spools almost empty** (with the list of spools), and **one sensor per spool** (remaining grams; brand, material, colour, storage location and — when loaded — printer and slot as attributes). Spools added on 3dsearch.net appear automatically; archived ones become unavailable.

The print event is based on the job history of 3dsearch.net, so a print that ends while Home Assistant restarts is still reported.

## Dashboard cards

The integration brings two cards along — no extra download, they appear in the card picker after the restart:

```yaml
type: custom:threedsearch-printer-card
device: <printer device>   # pick it in the visual editor
```

State, progress ring with remaining time and end, temperatures, the filament slots **in their real colours** with remaining grams, and pause/resume/cancel (cancel needs a second tap).

```yaml
type: custom:threedsearch-stock-card
```

Filament in stock and all your spools with colour, remaining grams and where they are (printer slot or storage location). Almost empty spools come first; with many spools the list folds after 8 rows (`rows: 12` to change).

## Installation

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/nolimitek/ha-3dsearch`, type **Integration**.
2. Install **3DSEARCH Printers & Filament** and restart Home Assistant.
3. On [3dsearch.net](https://3dsearch.net/filament/#settings) open **Printers & Filament → Settings → Home Assistant** and create a key.
4. In Home Assistant: **Settings → Devices & services → Add integration → 3DSEARCH** and paste the key.

The key gives read access to your printers and spools and can pause/resume/cancel prints. You can revoke it on 3dsearch.net at any time.

## Example automation

```yaml
triggers:
  - trigger: state
    entity_id: event.printsaurus_print
    attribute: event_type
    to: finished
actions:
  - action: notify.mobile_app_phone
    data:
      message: "{{ state_attr('event.printsaurus_print', 'job_name') }} is done"
```

## Notes

- Home Assistant polls every 60 seconds (adjustable in the integration options, 30–600 s). Printer clouds are synced by 3dsearch.net at most once a minute, so this is not a real-time integration.
- Printers & Filament is in beta on 3dsearch.net.

## Deutsch

Drucker und Filamentlager von [3dsearch.net](https://3dsearch.net/filament/) in Home Assistant. Installation über HACS (benutzerdefiniertes Repository, Typ Integration), danach auf 3dsearch.net unter **Drucker & Filament → Einstellungen → Home Assistant** einen Schlüssel erstellen und in Home Assistant bei **Integration hinzufügen → 3DSEARCH** einfügen. Die Integration ist auf Deutsch, Englisch, Französisch, Spanisch, Italienisch und Niederländisch übersetzt.

## License

GPL-3.0 — see [LICENSE](LICENSE).
