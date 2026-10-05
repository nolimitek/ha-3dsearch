/*
 * 3DSEARCH dashboard cards — shipped with the integration, loaded automatically (no extra HACS download).
 *
 *   type: custom:threedsearch-printer-card   device: <printer device id>   (one printer: state, progress, temperatures,
 *                                                                        slots in their real filament colours, buttons)
 *   type: custom:threedsearch-stock-card                                     (filament stock and spools that run low)
 *
 * Entities are found through the entity registry (platform "3dsearch" + translation key), so the cards work
 * whatever language Home Assistant used to name the entity ids. No external libraries, theme colours only.
 */
(() => {
"use strict";
const VERSION = "0.4.0";
const DOMAIN = "3dsearch";

const I18N = {
  en: { dry: "Dry", dryStop: "Stop drying", drying: "Drying", left: "{t} left", dryStart: "Start drying", dryCancel: "Close", dTemp: "Temperature", dHours: "Hours", humidity: "Humidity",
        all: "Show all ({n})", less: "Show less", lowN: "{n} almost empty", inSlot: "Slot", noSpools: "No spools yet.",
        remaining: "Remaining", ends: "Ends", layer: "Layer", nozzle: "Nozzle", bed: "Bed", pause: "Pause", resume: "Resume", cancel: "Cancel",
        sure: "Really cancel?", slots: "Filament", noSpool: "no spool", stock: "Filament stock", spools: "spools", low: "Almost empty",
        noLow: "No spool is running low.", pick: "Printer", pickHint: "Add a printer in the 3DSEARCH integration first.", lastSeen: "last seen",
        idle: "Idle", printing: "Printing", paused: "Paused", error: "Error", offline: "Offline", today: "today", tomorrow: "tomorrow" },
  de: { dry: "Trocknen", dryStop: "Trocknen stoppen", drying: "Trocknet", left: "noch {t}", dryStart: "Trocknen starten", dryCancel: "Schließen", dTemp: "Temperatur", dHours: "Stunden", humidity: "Feuchte",
        all: "Alle anzeigen ({n})", less: "Weniger anzeigen", lowN: "{n} fast leer", inSlot: "Fach", noSpools: "Noch keine Spulen.",
        remaining: "Restzeit", ends: "Ende", layer: "Schicht", nozzle: "Düse", bed: "Bett", pause: "Pause", resume: "Fortsetzen", cancel: "Abbrechen",
        sure: "Wirklich abbrechen?", slots: "Filament", noSpool: "keine Spule", stock: "Filamentlager", spools: "Spulen", low: "Fast leer",
        noLow: "Keine Spule ist fast leer.", pick: "Drucker", pickHint: "Lege zuerst in der 3DSEARCH-Integration einen Drucker an.", lastSeen: "zuletzt",
        idle: "Bereit", printing: "Druckt", paused: "Pausiert", error: "Fehler", offline: "Offline", today: "heute", tomorrow: "morgen" },
  fr: { dry: "Sécher", dryStop: "Arrêter le séchage", drying: "Séchage", left: "encore {t}", dryStart: "Lancer le séchage", dryCancel: "Fermer", dTemp: "Température", dHours: "Heures", humidity: "Humidité",
        all: "Tout afficher ({n})", less: "Afficher moins", lowN: "{n} presque vides", inSlot: "Empl.", noSpools: "Aucune bobine pour l’instant.",
        remaining: "Restant", ends: "Fin", layer: "Couche", nozzle: "Buse", bed: "Plateau", pause: "Pause", resume: "Reprendre", cancel: "Annuler",
        sure: "Vraiment annuler ?", slots: "Filament", noSpool: "pas de bobine", stock: "Stock de filament", spools: "bobines", low: "Presque vides",
        noLow: "Aucune bobine n’est presque vide.", pick: "Imprimante", pickHint: "Ajoutez d’abord une imprimante dans l’intégration 3DSEARCH.", lastSeen: "vue",
        idle: "Prête", printing: "Impression", paused: "En pause", error: "Erreur", offline: "Hors ligne", today: "aujourd’hui", tomorrow: "demain" },
  es: { dry: "Secar", dryStop: "Detener secado", drying: "Secando", left: "faltan {t}", dryStart: "Iniciar secado", dryCancel: "Cerrar", dTemp: "Temperatura", dHours: "Horas", humidity: "Humedad",
        all: "Mostrar todas ({n})", less: "Mostrar menos", lowN: "{n} casi vacías", inSlot: "Ranura", noSpools: "Todavía no hay bobinas.",
        remaining: "Restante", ends: "Fin", layer: "Capa", nozzle: "Boquilla", bed: "Cama", pause: "Pausa", resume: "Reanudar", cancel: "Cancelar",
        sure: "¿Cancelar de verdad?", slots: "Filamento", noSpool: "sin bobina", stock: "Stock de filamento", spools: "bobinas", low: "Casi vacías",
        noLow: "Ninguna bobina está casi vacía.", pick: "Impresora", pickHint: "Añade primero una impresora en la integración 3DSEARCH.", lastSeen: "vista",
        idle: "Lista", printing: "Imprimiendo", paused: "En pausa", error: "Error", offline: "Sin conexión", today: "hoy", tomorrow: "mañana" },
  it: { dry: "Essiccare", dryStop: "Ferma essiccazione", drying: "In essiccazione", left: "ancora {t}", dryStart: "Avvia essiccazione", dryCancel: "Chiudi", dTemp: "Temperatura", dHours: "Ore", humidity: "Umidità",
        all: "Mostra tutte ({n})", less: "Mostra meno", lowN: "{n} quasi vuote", inSlot: "Slot", noSpools: "Ancora nessuna bobina.",
        remaining: "Rimanente", ends: "Fine", layer: "Strato", nozzle: "Ugello", bed: "Piatto", pause: "Pausa", resume: "Riprendi", cancel: "Annulla",
        sure: "Annullare davvero?", slots: "Filamento", noSpool: "nessuna bobina", stock: "Scorte di filamento", spools: "bobine", low: "Quasi vuote",
        noLow: "Nessuna bobina è quasi vuota.", pick: "Stampante", pickHint: "Aggiungi prima una stampante nell’integrazione 3DSEARCH.", lastSeen: "vista",
        idle: "Pronta", printing: "In stampa", paused: "In pausa", error: "Errore", offline: "Offline", today: "oggi", tomorrow: "domani" },
  nl: { dry: "Drogen", dryStop: "Drogen stoppen", drying: "Droogt", left: "nog {t}", dryStart: "Drogen starten", dryCancel: "Sluiten", dTemp: "Temperatuur", dHours: "Uren", humidity: "Vocht",
        all: "Alles tonen ({n})", less: "Minder tonen", lowN: "{n} bijna leeg", inSlot: "Sleuf", noSpools: "Nog geen spoelen.",
        remaining: "Resterend", ends: "Einde", layer: "Laag", nozzle: "Nozzle", bed: "Bed", pause: "Pauze", resume: "Hervatten", cancel: "Annuleren",
        sure: "Echt annuleren?", slots: "Filament", noSpool: "geen spoel", stock: "Filamentvoorraad", spools: "spoelen", low: "Bijna leeg",
        noLow: "Geen spoel is bijna leeg.", pick: "Printer", pickHint: "Voeg eerst een printer toe in de 3DSEARCH-integratie.", lastSeen: "gezien",
        idle: "Gereed", printing: "Print", paused: "Gepauzeerd", error: "Fout", offline: "Offline", today: "vandaag", tomorrow: "morgen" },
};

const ICONS = {
  pause: "M14,19H18V5H14M6,19H10V5H6V19Z",
  play: "M8,5.14V19.14L19,12.14L8,5.14Z",
  stop: "M18,18H6V6H18V18Z",
  heat: "M15.24,19.66C14.4,20.5 13.25,21 12,21C9.24,21 7,18.76 7,16C7,13.97 8.22,12.24 9.97,11.46L11,16C11,16.55 11.45,17 12,17C12.55,17 13,16.55 13,16L14,11.45C15.75,12.22 17,13.96 17,16C17,17.25 16.5,18.4 15.66,19.24M12,2C12.55,2 13,2.45 13,3V5C13,5.55 12.55,6 12,6C11.45,6 11,5.55 11,5V3C11,2.45 11.45,2 12,2M7.05,4.64L8.46,6.05C8.85,6.44 8.85,7.07 8.46,7.46C8.07,7.85 7.44,7.85 7.05,7.46L5.64,6.05C5.25,5.66 5.25,5.03 5.64,4.64C6.03,4.25 6.66,4.25 7.05,4.64M16.95,4.64C17.34,4.25 17.97,4.25 18.36,4.64C18.75,5.03 18.75,5.66 18.36,6.05L16.95,7.46C16.56,7.85 15.93,7.85 15.54,7.46C15.15,7.07 15.15,6.44 15.54,6.05L16.95,4.64Z",
  drop: "M12,20A6,6 0 0,1 6,14C6,10 12,3.25 12,3.25C12,3.25 18,10 18,14A6,6 0 0,1 12,20Z",
  nozzle: "M7,2H17V8H19V13H16.5L13,17H11L7.5,13H5V8H7V2M10,22H2V20H10A1,1 0 0,0 11,19V18H13V19A3,3 0 0,1 10,22Z",
  bed: "M2,20V17H22V20H20V22H18V20H6V22H4V20H2M7,12A3,3 0 0,1 10,15H14A3,3 0 0,1 17,12V15H7V12M5,8H19V10H5V8Z",
  layers: "M12,16L19.36,10.27L21,9L12,2L3,9L4.63,10.27M12,18.54L4.62,12.81L3,14.07L12,21.07L21,14.07L19.37,12.8L12,18.54Z",
  printer: "M19,6A1,1 0 0,0 20,5A1,1 0 0,0 19,4A1,1 0 0,0 18,5A1,1 0 0,0 19,6M19,2A3,3 0 0,1 22,5V11H18V7H6V11H2V5A3,3 0 0,1 5,2H19M18,18.25C18,18.63 17.79,18.96 17.47,19.13L12.57,21.82C12.4,21.94 12.21,22 12,22C11.79,22 11.59,21.94 11.43,21.82L6.53,19.13C6.21,18.96 6,18.63 6,18.25V13C6,12.62 6.21,12.29 6.53,12.12L11.43,9.68C11.59,9.56 11.79,9.5 12,9.5C12.21,9.5 12.4,9.56 12.57,9.68L17.47,12.12C17.79,12.29 18,12.62 18,13V18.25M12,11.65L9.04,13L12,14.6L14.96,13L12,11.65M8,17.66L11,19.29V16.33L8,14.71V17.66M16,17.66V14.71L13,16.33V19.29L16,17.66Z",
};

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const hex = (c) => (typeof c === "string" && /^#[0-9a-f]{6}$/i.test(c) ? c : null);
const svg = (d, size = 18) => `<svg viewBox="0 0 24 24" width="${size}" height="${size}" aria-hidden="true"><path fill="currentColor" d="${d}"/></svg>`;
const usable = (st) => st && st.state !== "unavailable" && st.state !== "unknown";

/** Filament spool in its real colour; the winding shrinks with the remaining amount (same drawing as the entity pictures). */
function spoolSvg(color, percent, size) {
  const c = hex(color);
  if (!c) return `<span class="spool none" style="width:${size}px;height:${size}px"></span>`;
  const p = typeof percent === "number" ? Math.max(0, Math.min(100, percent)) : 100;
  const hub = 7.5, full = 17.5, r = hub + 2.0 + (full - hub - 2.0) * p / 100;
  const lines = [1, 2, 3, 4].map((i) => hub + 2.2 * i).filter((x) => x < r - 0.8)
    .map((x) => `<circle cx="20" cy="20" r="${x.toFixed(1)}" fill="none" stroke="#000" stroke-opacity=".13" stroke-width=".6"/>`).join("");
  return `<svg class="spool" viewBox="0 0 40 40" width="${size}" height="${size}" aria-hidden="true"><circle cx="20" cy="20" r="19.5" fill="#5b6370"/>
    <circle cx="20" cy="20" r="${full}" fill="#c7ccd4"/>${p > 0 ? `<circle cx="20" cy="20" r="${r.toFixed(1)}" fill="${c}"/>${lines}` : ""}
    <circle cx="20" cy="20" r="${hub}" fill="#5b6370"/><circle cx="20" cy="20" r="3.2" fill="#eef0f3"/></svg>`;
}

function lang(hass) {
  const l = (hass?.locale?.language || hass?.language || "en").slice(0, 2);
  return I18N[l] ? l : "en";
}

/** All 3DSEARCH entities of one device, by translation key (slots as a list). */
function deviceEntities(hass, deviceId) {
  const out = { slots: [] };
  for (const e of Object.values(hass.entities || {})) {
    if (e.platform !== DOMAIN || e.device_id !== deviceId) continue;
    if (e.translation_key === "slot") out.slots.push(e.entity_id);
    else if (e.translation_key && e.translation_key.startsWith("box_")) {
      const bid = hass.states[e.entity_id]?.attributes.box_id;
      if (bid === undefined) continue;
      (out.boxes ||= {})[bid] ||= { label: hass.states[e.entity_id].attributes.box };
      out.boxes[bid][e.translation_key.slice(4)] = e.entity_id;
    } else if (e.translation_key) out[e.translation_key] = e.entity_id;
  }
  out.slots.sort((a, b) => (hass.states[a]?.attributes.index ?? 0) - (hass.states[b]?.attributes.index ?? 0));
  return out;
}

/** Printer devices of the integration (devices that have a 3DSEARCH status sensor). */
function printerDevices(hass) {
  const ids = new Set();
  for (const e of Object.values(hass.entities || {})) if (e.platform === DOMAIN && e.translation_key === "status" && e.device_id) ids.add(e.device_id);
  return [...ids].map((id) => ({ id, name: deviceName(hass, id) })).sort((a, b) => a.name.localeCompare(b.name));
}

function deviceName(hass, id) {
  const d = hass.devices?.[id];
  return d ? d.name_by_user || d.name || id : id;
}

function fmtMinutes(min, l) {
  const m = Math.max(0, Math.round(+min));
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60), r = m % 60;
  return `${h} h${r ? ` ${String(r).padStart(2, "0")} min` : ""}`;
}

function fmtEnd(iso, hass, t) {
  const d = new Date(iso);
  if (isNaN(d)) return "";
  const loc = hass?.locale?.language || "en";
  const time = d.toLocaleTimeString(loc, { hour: "2-digit", minute: "2-digit" });
  const day = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const diff = Math.round((day(d) - day(new Date())) / 864e5);
  if (diff === 0) return time;
  if (diff === 1) return `${t.tomorrow} ${time}`;
  return `${d.toLocaleDateString(loc, { weekday: "short" })} ${time}`;
}

function fmtNum(v, hass, digits = 0) {
  return Number(v).toLocaleString(hass?.locale?.language || "en", { maximumFractionDigits: digits });
}

function moreInfo(el, entityId) {
  if (!entityId) return;
  el.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
}

const BASE_CSS = `
  :host { display: block; }
  ha-card { padding: 16px; }
  .head { display: flex; align-items: center; gap: 12px; }
  .ico { width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center; flex: none;
         background: color-mix(in srgb, var(--state-color) 16%, transparent); color: var(--state-color); }
  .tt { flex: 1; min-width: 0; cursor: pointer; }
  .name { font-size: 16px; font-weight: 600; color: var(--primary-text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .sub { font-size: 12px; color: var(--secondary-text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .pill { flex: none; display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600;
          background: color-mix(in srgb, var(--state-color) 14%, transparent); color: var(--state-color); cursor: pointer; }
  .pill i { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
  .muted { color: var(--secondary-text-color); font-size: 13px; }
  .sec { margin-top: 14px; }
  .lbl { font-size: 11px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; color: var(--secondary-text-color); margin-bottom: 8px; }
  button { font: inherit; }
  .spool { display: block; flex: none; }
  .spool.none { box-sizing: border-box; border-radius: 50%; border: 2px dashed var(--divider-color, rgba(127,127,127,.4)); }
`;

// ── Printer card ─────────────────────────────────────────────────────────────
class ThreeDSearchPrinterCard extends HTMLElement {
  static getConfigElement() { return document.createElement("threedsearch-printer-card-editor"); }

  static getStubConfig(hass) {
    const first = printerDevices(hass)[0];
    return { device: first ? first.id : "" };
  }

  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    this._config = { ...config };
    this._sig = null;
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    // Only re-render when one of this printer's entities changed (hass is set on every state change in HA)
    const ents = this._config?.device ? deviceEntities(hass, this._config.device) : null;
    const boxIds = ents ? Object.values(ents.boxes || {}).flatMap((b) => Object.entries(b).filter(([k]) => k !== "label").map(([, v]) => v)) : [];
    const ids = ents ? [ents.status, ents.progress, ents.remaining_time, ents.end_time, ents.job_name, ents.current_layer,
      ents.nozzle_temperature, ents.bed_temperature, ents.pause, ents.resume, ents.cancel, ...ents.slots, ...boxIds] : [];
    const sig = ids.map((id) => (id && hass.states[id] ? hass.states[id].last_updated + hass.states[id].state : "")).join("|") + (hass.locale?.language || "");
    if (sig === this._sig) return;
    this._sig = sig;
    this._ents = ents;
    this._render();
  }

  getCardSize() { return 5; }
  getGridOptions() { return { columns: 12, min_columns: 6, rows: "auto" }; }

  _st(key) { const id = this._ents?.[key]; return id ? this._hass.states[id] : undefined; }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const hass = this._hass, t = I18N[lang(hass)];
    if (!this._config.device || !this._ents?.status) {
      this.shadowRoot.innerHTML = `<style>${BASE_CSS}</style><ha-card><div class="muted">${esc(t.pickHint)}</div></ha-card>`;
      return;
    }
    const st = this._st("status");
    const state = st?.state ?? "unavailable";
    const known = ["idle", "printing", "paused", "error", "offline"].includes(state);
    const label = known ? (hass.formatEntityState ? hass.formatEntityState(st) : t[state]) : (hass.formatEntityState && st ? hass.formatEntityState(st) : state);
    const color = { idle: "var(--success-color, #43a047)", printing: "var(--primary-color, #03a9f4)", paused: "var(--warning-color, #ffa600)",
                    error: "var(--error-color, #db4437)" }[state] || "var(--secondary-text-color, #727272)";
    const dev = hass.devices?.[this._config.device] || {};
    const sub = [dev.model, dev.manufacturer].filter(Boolean).join(" · ");
    const active = state === "printing" || state === "paused";

    let job = "";
    if (active) {
      const pr = this._st("progress"), rt = this._st("remaining_time"), en = this._st("end_time"), jn = this._st("job_name"), ly = this._st("current_layer");
      const pct = usable(pr) ? Math.max(0, Math.min(100, +pr.state)) : 0;
      const r = 34, c = 2 * Math.PI * r;
      const facts = [];
      if (usable(rt)) facts.push(`<span><b>${esc(fmtMinutes(rt.state))}</b> ${esc(t.remaining)}</span>`);
      if (usable(en) && state === "printing") facts.push(`<span>${esc(t.ends)} <b>${esc(fmtEnd(en.state, hass, t))}</b></span>`);
      if (usable(ly)) facts.push(`<span>${svg(ICONS.layers, 14)} ${esc(t.layer)} <b>${esc(ly.state)}${ly.attributes.total_layers ? ` / ${esc(ly.attributes.total_layers)}` : ""}</b></span>`);
      job = `<div class="job sec">
        <div class="ring" data-more="progress" role="img" aria-label="${pct}%">
          <svg viewBox="0 0 80 80" width="80" height="80"><circle cx="40" cy="40" r="${r}" class="trk"/>
            <circle cx="40" cy="40" r="${r}" class="bar" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - pct / 100)}"/></svg>
          <span>${pct}<small>%</small></span></div>
        <div class="jt"><div class="jname" data-more="job_name">${esc(usable(jn) ? jn.state : "")}</div><div class="facts">${facts.join("")}</div></div>
      </div>`;
    }

    const temps = [["nozzle_temperature", ICONS.nozzle, t.nozzle], ["bed_temperature", ICONS.bed, t.bed]]
      .map(([k, ic, lb]) => { const s = this._st(k); return usable(s) ? `<button class="chip" data-more="${k}" title="${esc(lb)}">${svg(ic, 16)}<span>${esc(lb)}</span><b>${esc(fmtNum(s.state, hass))} ${esc(s.attributes.unit_of_measurement || "")}</b></button>` : ""; })
      .join("");

    const slots = (this._ents.slots || []).map((id) => {
      const s = hass.states[id];
      if (!s || s.state === "unavailable") return "";
      const a = s.attributes, col = hex(a.color);
      const pct = typeof a.remaining_percent === "number" ? Math.max(0, Math.min(100, a.remaining_percent)) : null;
      const grams = usable(s) ? `${fmtNum(s.state, hass)} g` : t.noSpool;
      return `<button class="slot" data-id="${esc(id)}" title="${esc([a.spool_name, a.brand].filter(Boolean).join(" · ") || a.material || "")}">
        ${spoolSvg(col, pct, 34)}
        <span class="sl">${esc(a.slot ?? "")}</span>
        <span class="mat">${esc(a.material || "–")}</span>
        <span class="g">${esc(grams)}</span>
        ${pct !== null ? `<span class="fill${pct <= 15 ? " low" : ""}"><i style="width:${pct}%"></i></span>` : ""}
      </button>`;
    }).join("");

    const btn = (key, icon, text, cls = "") => {
      const s = this._st(key);
      if (!s) return "";
      const ok = s.state !== "unavailable";   // pause only while printing, resume only while paused …
      return `<button class="act ${cls}" data-press="${key}"${ok ? "" : " disabled"}>${svg(icon, 16)}<span>${esc(this._confirm === key ? t.sure : text)}</span></button>`;
    };
    const actions = btn("pause", ICONS.pause, t.pause) + btn("resume", ICONS.play, t.resume) + btn("cancel", ICONS.stop, t.cancel, "danger");

    const err = state === "error" && st.attributes.error ? `<div class="err sec">${esc(st.attributes.error)}</div>` : "";
    const seen = state === "offline" && st.attributes.last_update
      ? `<div class="muted sec">${esc(t.lastSeen)} ${esc(new Date(st.attributes.last_update).toLocaleString(hass.locale?.language || "en", { dateStyle: "short", timeStyle: "short" }))}</div>` : "";

    this.shadowRoot.innerHTML = `<style>${BASE_CSS}${PRINTER_CSS}</style>
      <ha-card style="--state-color:${color}" class="${state === "offline" ? "off" : ""}">
        <div class="head">
          <span class="ico">${svg(ICONS.printer, 22)}</span>
          <div class="tt" data-more="status"><div class="name">${esc(this._config.name || deviceName(hass, this._config.device))}</div>${sub ? `<div class="sub">${esc(sub)}</div>` : ""}</div>
          <span class="pill" data-more="status"><i></i>${esc(label)}</span>
        </div>
        ${err}${job}
        ${temps ? `<div class="chips sec">${temps}</div>` : ""}
        ${slots ? `<div class="sec"><div class="lbl">${esc(t.slots)}</div><div class="slots">${slots}</div></div>` : ""}
        ${this._boxesHtml(t)}
        ${actions ? `<div class="acts sec">${actions}</div>` : ""}
        ${seen}
      </ha-card>`;

    this.shadowRoot.querySelectorAll("[data-more]").forEach((el) => el.addEventListener("click", () => moreInfo(this, this._ents[el.dataset.more])));
    this.shadowRoot.querySelectorAll("[data-id]").forEach((el) => el.addEventListener("click", () => moreInfo(this, el.dataset.id)));
    this.shadowRoot.querySelectorAll("[data-press]").forEach((el) => el.addEventListener("click", () => this._press(el.dataset.press)));
    this._bindBoxes();
  }

  /** One block per ACE/AMS: climate, drying state, and for ACE the drying controls with presets. */
  _boxesHtml(t) {
    const hass = this._hass, boxes = this._ents.boxes || {};
    return Object.entries(boxes).sort(([a], [b]) => a - b).map(([bid, b]) => {
      const st = (k) => (b[k] ? hass.states[b[k]] : undefined);
      const sw = st("drying"), rem = st("dry_remaining"), tmp = st("temperature"), hum = st("humidity");
      const ctl = !!sw && sw.state !== "unavailable";
      const drying = ctl ? sw.state === "on" : !!rem?.attributes.drying;
      const target = (ctl ? sw.attributes.target_temperature : rem?.attributes.target_temperature) || null;
      const left = (ctl ? sw.attributes.remaining_minutes : usable(rem) ? +rem.state : null) || null;
      const chips = [usable(tmp) ? `<span class="mini" data-eid="${esc(b.temperature)}">${svg(ICONS.heat, 14)}${esc(fmtNum(tmp.state, hass))} °C</span>` : "",
                     usable(hum) ? `<span class="mini" data-eid="${esc(b.humidity)}">${svg(ICONS.drop, 14)}${esc(fmtNum(hum.state, hass))} %</span>` : ""].join("");
      if (!ctl && !drying && !chips) return "";
      const open = this._dryOpen === bid && ctl && !drying;
      const v = this._dryVals?.[bid] || { temp: +(st("dry_temperature")?.state) || 45, hours: +(st("dry_duration")?.state) || 4 };
      const presets = [["PLA", 45, 4], ["TPU", 50, 6], ["PETG", 55, 6], ["ABS/ASA", 55, 8]];
      return `<div class="sec box" data-box="${esc(bid)}">
        <div class="bxh"><b>${esc(b.label || "Box")}</b>${chips}<span class="grow"></span>
          ${ctl ? (drying ? `<button class="act sm danger" data-dry="stop">${svg(ICONS.stop, 14)}<span>${esc(t.dryStop)}</span></button>`
                          : `<button class="act sm" data-dry="${open ? "close" : "open"}">${svg(ICONS.heat, 14)}<span>${esc(open ? t.dryCancel : t.dry)}</span></button>`) : ""}</div>
        ${drying ? `<div class="dryon" data-eid="${esc(b.drying || b.dry_remaining)}">${svg(ICONS.heat, 16)}<span><b>${esc(t.drying)}</b>${target ? ` · ${esc(target)} °C` : ""}${left ? ` · ${esc(t.left.replace("{t}", fmtMinutes(left)))}` : ""}</span></div>` : ""}
        ${open ? `<div class="drypanel">
            <div class="presets">${presets.map(([m, tc, hh]) => `<button data-pre="${tc},${hh}" class="${v.temp === tc && v.hours === hh ? "on" : ""}"><b>${m}</b><span>${tc} °C · ${hh} h</span></button>`).join("")}</div>
            <div class="dryin"><label>${esc(t.dTemp)}<input type="number" min="35" max="55" step="1" value="${esc(v.temp)}" data-in="temp"> °C</label>
              <label>${esc(t.dHours)}<input type="number" min="1" max="24" step="1" value="${esc(v.hours)}" data-in="hours"> h</label>
              <button class="act pri" data-dry="start">${svg(ICONS.heat, 16)}<span>${esc(t.dryStart)}</span></button></div>
          </div>` : ""}
      </div>`;
    }).join("");
  }

  _bindBoxes() {
    const root = this.shadowRoot;
    root.querySelectorAll("[data-eid]").forEach((el) => el.addEventListener("click", () => moreInfo(this, el.dataset.eid)));
    root.querySelectorAll(".box").forEach((boxEl) => {
      const bid = boxEl.dataset.box, b = this._ents.boxes[bid];
      const vals = () => (this._dryVals ||= {})[bid] ||= { temp: +(this._hass.states[b.dry_temperature]?.state) || 45, hours: +(this._hass.states[b.dry_duration]?.state) || 4 };
      boxEl.querySelectorAll("[data-pre]").forEach((el) => el.addEventListener("click", () => {
        const [tc, hh] = el.dataset.pre.split(",").map(Number); Object.assign(vals(), { temp: tc, hours: hh }); this._sig = null; this._render();
      }));
      boxEl.querySelectorAll("[data-in]").forEach((el) => el.addEventListener("change", () => { vals()[el.dataset.in] = +el.value; }));
      boxEl.querySelectorAll("[data-dry]").forEach((el) => el.addEventListener("click", async () => {
        const a = el.dataset.dry;
        if (a === "open" || a === "close") { this._dryOpen = a === "open" ? bid : null; this._sig = null; this._render(); return; }
        el.disabled = true;
        try {
          if (a === "start") {
            const v = vals();
            const temp = Math.max(35, Math.min(55, Math.round(v.temp || 45))), hours = Math.max(1, Math.min(24, Math.round(v.hours || 4)));
            if (b.dry_temperature) await this._hass.callService("number", "set_value", { entity_id: b.dry_temperature, value: temp });
            if (b.dry_duration) await this._hass.callService("number", "set_value", { entity_id: b.dry_duration, value: hours });
            await this._hass.callService("switch", "turn_on", { entity_id: b.drying });
            this._dryOpen = null;
          } else {
            await this._hass.callService("switch", "turn_off", { entity_id: b.drying });
          }
        } finally { this._sig = null; this._render(); }
      }));
    });
  }

  _press(key) {
    // Cancel needs a second click within 4 s — a mis-tap must not end a 10-hour print
    if (key === "cancel" && this._confirm !== "cancel") {
      this._confirm = "cancel";
      clearTimeout(this._confirmTimer);
      this._confirmTimer = setTimeout(() => { this._confirm = null; this._render(); }, 4000);
      this._render();
      return;
    }
    this._confirm = null;
    clearTimeout(this._confirmTimer);
    this._hass.callService("button", "press", { entity_id: this._ents[key] });
    this._render();
  }
}

const PRINTER_CSS = `
  ha-card.off .sec:not(.muted) { opacity: .55; }
  .job { display: flex; align-items: center; gap: 16px; }
  .ring { position: relative; width: 80px; height: 80px; flex: none; cursor: pointer; }
  .ring svg { transform: rotate(-90deg); }
  .ring circle { fill: none; stroke-width: 8; }
  .ring .trk { stroke: var(--divider-color, rgba(127,127,127,.25)); }
  .ring .bar { stroke: var(--state-color); stroke-linecap: round; transition: stroke-dashoffset .6s ease; }
  .ring span { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 700; color: var(--primary-text-color); }
  .ring small { font-size: 11px; font-weight: 600; color: var(--secondary-text-color); margin-left: 1px; }
  .jt { min-width: 0; flex: 1; }
  .jname { font-weight: 600; color: var(--primary-text-color); overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; cursor: pointer; }
  .facts { display: flex; flex-wrap: wrap; gap: 4px 14px; margin-top: 6px; font-size: 13px; color: var(--secondary-text-color); }
  .facts span { display: inline-flex; align-items: center; gap: 4px; }
  .facts b { color: var(--primary-text-color); font-weight: 600; }
  .chips { display: flex; gap: 8px; flex-wrap: wrap; }
  .chip { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px; border: 0; cursor: pointer;
          background: var(--secondary-background-color, rgba(127,127,127,.1)); color: var(--secondary-text-color); font-size: 13px; }
  .chip b { color: var(--primary-text-color); font-weight: 600; }
  .slots { display: grid; grid-template-columns: repeat(auto-fill, minmax(76px, 1fr)); gap: 8px; }
  .slot { display: grid; justify-items: center; gap: 2px; padding: 10px 6px 8px; border-radius: 12px; cursor: pointer; text-align: center;
          border: 1px solid var(--divider-color, rgba(127,127,127,.25)); background: none; color: var(--primary-text-color); min-width: 0; }
  .slot .spool { margin-bottom: 4px; }
  .sl { font-size: 11px; color: var(--secondary-text-color); }
  .mat { font-size: 13px; font-weight: 600; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .g { font-size: 12px; color: var(--secondary-text-color); white-space: nowrap; }
  .fill { width: 80%; height: 4px; border-radius: 2px; background: var(--divider-color, rgba(127,127,127,.25)); overflow: hidden; margin-top: 4px; }
  .fill i { display: block; height: 100%; border-radius: 2px; background: var(--primary-color, #03a9f4); }
  .fill.low i { background: var(--warning-color, #ffa600); }
  .acts { display: flex; gap: 8px; flex-wrap: wrap; }
  .act { flex: 1 1 110px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 9px 12px; border-radius: 10px; cursor: pointer;
         border: 1px solid var(--divider-color, rgba(127,127,127,.3)); background: none; color: var(--primary-text-color); font-weight: 600; font-size: 13px; }
  .act:hover { background: var(--secondary-background-color, rgba(127,127,127,.08)); }
  .act.danger { color: var(--error-color, #db4437); }
  .act:disabled { opacity: .4; cursor: default; background: none; }
  .act.sm { flex: none; padding: 6px 10px; font-size: 12px; }
  .act.pri { flex: none; background: var(--primary-color, #03a9f4); border-color: transparent; color: var(--text-primary-color, #fff); }
  .box { border: 1px solid var(--divider-color, rgba(127,127,127,.25)); border-radius: 12px; padding: 10px 12px; }
  .bxh { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .bxh > b { font-size: 14px; color: var(--primary-text-color); }
  .grow { flex: 1; }
  .mini { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; color: var(--secondary-text-color); cursor: pointer;
          padding: 2px 8px; border-radius: 999px; background: var(--secondary-background-color, rgba(127,127,127,.1)); }
  .dryon { display: flex; align-items: center; gap: 8px; margin-top: 8px; padding: 8px 10px; border-radius: 10px; font-size: 13px; cursor: pointer;
           color: var(--warning-color, #ffa600); background: color-mix(in srgb, var(--warning-color, #ffa600) 12%, transparent); }
  .dryon span { color: var(--primary-text-color); }
  .drypanel { margin-top: 10px; display: grid; gap: 10px; }
  .presets { display: grid; grid-template-columns: repeat(auto-fit, minmax(92px, 1fr)); gap: 6px; }
  .presets button { display: grid; gap: 2px; padding: 8px; border-radius: 10px; cursor: pointer; text-align: left;
                    border: 1px solid var(--divider-color, rgba(127,127,127,.3)); background: none; color: var(--primary-text-color); }
  .presets button span { font-size: 12px; color: var(--secondary-text-color); }
  .presets button.on { border-color: var(--primary-color, #03a9f4); box-shadow: 0 0 0 1px var(--primary-color, #03a9f4); }
  .dryin { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; font-size: 13px; color: var(--secondary-text-color); }
  .dryin label { display: inline-flex; align-items: center; gap: 6px; }
  .dryin input { width: 56px; font: inherit; padding: 6px 8px; border-radius: 8px; border: 1px solid var(--divider-color, rgba(127,127,127,.4));
                 background: var(--card-background-color, #fff); color: var(--primary-text-color); }
  .dryin .act { margin-left: auto; }
  .err { padding: 10px 12px; border-radius: 10px; font-size: 13px; color: var(--error-color, #db4437);
         background: color-mix(in srgb, var(--error-color, #db4437) 10%, transparent); overflow-wrap: anywhere; }
`;

// ── Stock card ───────────────────────────────────────────────────────────────
class ThreeDSearchStockCard extends HTMLElement {
  static getStubConfig() { return {}; }
  setConfig(config) { this._config = { rows: 8, ...(config || {}) }; this._sig = null; if (this._hass) this._render(); }

  set hass(hass) {
    this._hass = hass;
    const ids = { spool: [] };
    for (const e of Object.values(hass.entities || {})) {
      if (e.platform !== DOMAIN) continue;
      if (e.translation_key === "spool") ids.spool.push(e.entity_id);
      else if (["spools", "filament_stock", "low_spools"].includes(e.translation_key)) ids[e.translation_key] = e.entity_id;
    }
    this._ids = ids;
    const sig = [ids.spools, ids.filament_stock, ids.low_spools, ...ids.spool].map((id) => (id && hass.states[id] ? hass.states[id].last_updated + hass.states[id].state : "")).join("|")
      + (hass.locale?.language || "") + (this._open ? "1" : "0");
    if (sig === this._sig) return;
    this._sig = sig;
    this._render();
  }

  getCardSize() { return 4; }
  getGridOptions() { return { columns: 6, min_columns: 4, rows: "auto" }; }

  _render() {
    if (!this._hass) return;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const hass = this._hass, t = I18N[lang(hass)];
    const st = (k) => (this._ids[k] ? hass.states[this._ids[k]] : undefined);
    const stock = st("filament_stock"), count = st("spools"), low = st("low_spools");
    const kg = usable(stock) ? (stock.attributes.unit_of_measurement === "kg" ? +stock.state : +stock.state / 1000) : null;
    const thr = (usable(low) && +low.attributes.threshold_g) || 150;

    const isLow = (x) => x.g !== null && x.g < thr;
    // Order: almost empty → loaded in a printer → by storage location → without location
    const group = (x) => (isLow(x) ? 0 : x.a.printer ? 1 : x.a.location ? 2 : 3);
    const spools = this._ids.spool.map((id) => hass.states[id]).filter((s) => s && s.state !== "unavailable")
      .map((s) => ({ id: s.entity_id, g: usable(s) ? +s.state : null, a: s.attributes }))
      .sort((x, y) => group(x) - group(y)
        || String(x.a.printer || x.a.location || "").localeCompare(String(y.a.printer || y.a.location || ""))
        || String(x.a.slot || "").localeCompare(String(y.a.slot || ""), undefined, { numeric: true })
        || String(x.a.spool_name || "").localeCompare(String(y.a.spool_name || "")));
    const nLow = spools.filter(isLow).length;
    const shown = this._open ? spools : spools.slice(0, Math.max(1, +this._config.rows || 8));
    const row = (x) => {
      const a = x.a, col = hex(a.color);
      const where = a.printer ? `${esc(a.printer)} · ${esc(t.inSlot)} ${esc(a.slot ?? "")}` : esc(a.location || "");
      const meta = [a.material, a.brand].filter(Boolean).map(esc).join(" · ");
      const pct = typeof a.remaining_percent === "number" ? Math.max(0, Math.min(100, a.remaining_percent)) : null;
      return `<li data-id="${esc(x.id)}" class="${isLow(x) ? "low" : ""}">
        ${spoolSvg(col, typeof a.remaining_percent === "number" ? a.remaining_percent : null, 28)}
        <span class="ln"><b>${esc(a.spool_name || "")}</b><small>${meta}${meta && where ? " · " : ""}${a.printer ? `<em>${where}</em>` : where}</small></span>
        <span class="lg"><b>${x.g !== null ? esc(fmtNum(x.g, hass)) + " g" : "–"}</b>${pct !== null ? `<span class="fill"><i style="width:${pct}%"></i></span>` : ""}</span>
      </li>`;
    };
    // Fallback for servers without the spool list: the old "almost empty" list
    const fallback = !spools.length && usable(low) && Array.isArray(low.attributes.spools) && low.attributes.spools.length
      ? low.attributes.spools.map((s) => row({ id: this._ids.low_spools, g: s.left_g, a: { spool_name: s.name, material: s.material, color: s.color } })).join("") : "";

    this.shadowRoot.innerHTML = `<style>${BASE_CSS}${STOCK_CSS}</style>
      <ha-card style="--state-color:var(--primary-color, #03a9f4)">
        <div class="lbl">${esc(this._config.title || t.stock)}</div>
        <div class="big"><b data-more="filament_stock">${kg !== null ? esc(fmtNum(kg, hass, 1)) : "–"}</b><span>kg</span>
          <em>${usable(count) ? `<span data-more="spools">${esc(fmtNum(count.state, hass))} ${esc(t.spools)}</span>` : ""}${nLow ? `<span class="lowchip" data-more="low_spools">${esc(t.lowN.replace("{n}", nLow))}</span>` : ""}</em></div>
        ${spools.length || fallback ? `<ul class="sec">${spools.length ? shown.map(row).join("") : fallback}</ul>` : `<div class="muted sec">${esc(t.noSpools)}</div>`}
        ${spools.length > shown.length || this._open ? `<button class="more">${esc(this._open ? t.less : t.all.replace("{n}", spools.length))}</button>` : ""}
      </ha-card>`;
    this.shadowRoot.querySelectorAll("[data-more]").forEach((el) => el.addEventListener("click", () => moreInfo(this, this._ids[el.dataset.more])));
    this.shadowRoot.querySelectorAll("li[data-id]").forEach((el) => el.addEventListener("click", () => moreInfo(this, el.dataset.id)));
    const more = this.shadowRoot.querySelector(".more");
    if (more) more.addEventListener("click", () => { this._open = !this._open; this._sig = null; this._render(); });
  }
}

const STOCK_CSS = `
  .big { display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; }
  .big > b { font-size: 34px; font-weight: 700; color: var(--primary-text-color); line-height: 1.1; cursor: pointer; }
  .big > span { font-size: 15px; color: var(--secondary-text-color); font-weight: 600; }
  .big em { font-style: normal; margin-left: auto; display: flex; gap: 8px; align-items: center; font-size: 13px; color: var(--secondary-text-color); }
  .big em span { cursor: pointer; }
  .lowchip { padding: 2px 9px; border-radius: 999px; font-weight: 600; color: var(--warning-color, #ffa600);
             background: color-mix(in srgb, var(--warning-color, #ffa600) 14%, transparent); }
  ul { list-style: none; margin: 14px 0 0; padding: 0; display: grid; }
  li { display: flex; align-items: center; gap: 10px; padding: 8px 0; min-width: 0; cursor: pointer;
       border-top: 1px solid var(--divider-color, rgba(127,127,127,.18)); }
  li:first-child { border-top: 0; }
  li .spool { flex: none; }
  .ln { flex: 1; min-width: 0; display: grid; }
  .ln b { font-size: 14px; font-weight: 600; color: var(--primary-text-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ln small { font-size: 12px; color: var(--secondary-text-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ln em { font-style: normal; color: var(--primary-color, #03a9f4); font-weight: 600; }
  .lg { flex: none; display: grid; justify-items: end; gap: 4px; min-width: 64px; }
  .lg b { font-size: 14px; font-weight: 600; color: var(--primary-text-color); white-space: nowrap; }
  .fill { width: 64px; height: 4px; border-radius: 2px; background: var(--divider-color, rgba(127,127,127,.25)); overflow: hidden; }
  .fill i { display: block; height: 100%; border-radius: 2px; background: var(--primary-color, #03a9f4); }
  li.low .lg b { color: var(--error-color, #db4437); }
  li.low .fill i { background: var(--warning-color, #ffa600); }
  .more { margin-top: 10px; width: 100%; padding: 9px; border-radius: 10px; cursor: pointer; font-weight: 600; font-size: 13px;
          border: 1px solid var(--divider-color, rgba(127,127,127,.3)); background: none; color: var(--primary-color, #03a9f4); }
`;

// ── Editor: pick the printer (plain <select>, no internal HA components needed) ──
class ThreeDSearchPrinterCardEditor extends HTMLElement {
  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(hass) { const first = !this._hass; this._hass = hass; if (first) this._render(); }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const t = I18N[lang(this._hass)], devs = printerDevices(this._hass);
    this.shadowRoot.innerHTML = `<style>
        label { display: grid; gap: 6px; font-size: 14px; color: var(--primary-text-color); }
        select { font: inherit; padding: 10px; border-radius: 8px; border: 1px solid var(--divider-color, #ccc);
                 background: var(--card-background-color, #fff); color: var(--primary-text-color); }
        p { color: var(--secondary-text-color); font-size: 13px; }
      </style>
      ${devs.length ? `<label>${esc(t.pick)}<select>${devs.map((d) => `<option value="${esc(d.id)}"${d.id === this._config.device ? " selected" : ""}>${esc(d.name)}</option>`).join("")}</select></label>`
                    : `<p>${esc(t.pickHint)}</p>`}`;
    const sel = this.shadowRoot.querySelector("select");
    if (sel) {
      if (!this._config.device && devs[0]) this._changed(devs[0].id);
      sel.addEventListener("change", () => this._changed(sel.value));
    }
  }

  _changed(device) {
    this._config = { ...this._config, device };
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
  }
}

for (const [tag, cls] of [["threedsearch-printer-card", ThreeDSearchPrinterCard], ["threedsearch-stock-card", ThreeDSearchStockCard],
                          ["threedsearch-printer-card-editor", ThreeDSearchPrinterCardEditor]]) {
  if (!customElements.get(tag)) customElements.define(tag, cls);
}
window.customCards = window.customCards || [];
for (const c of [
  { type: "threedsearch-printer-card", name: "3DSEARCH printer", description: "Printer state, progress, temperatures and filament slots in their real colours.", preview: true, documentationURL: "https://github.com/nolimitek/ha-3dsearch" },
  { type: "threedsearch-stock-card", name: "3DSEARCH filament stock", description: "All spools with colour and remaining filament; almost empty ones first.", preview: true, documentationURL: "https://github.com/nolimitek/ha-3dsearch" },
]) if (!window.customCards.some((x) => x.type === c.type)) window.customCards.push(c);
console.info(`%c 3DSEARCH cards %c ${VERSION} `, "background:#ff7a1a;color:#fff;font-weight:700;border-radius:3px 0 0 3px", "background:#333;color:#fff;border-radius:0 3px 3px 0");
})();
