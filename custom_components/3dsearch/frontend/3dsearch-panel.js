/* 3DSEARCH sidebar panel "3D printing": the 3DSEARCH workshop (printers, spools, slicer, print queue) in a frame.
 *
 * Signs in with a short-lived token from the integration (websocket 3dsearch/embed); the API key stays in Home
 * Assistant. The token goes in the URL fragment, which browsers never send to a server. When it expires, the workshop
 * posts "3dsearch-embed-expired" and the panel fetches a new one and reloads the frame on the same view.
 *
 * The frame sends this Home Assistant's origin as referer (referrerpolicy="origin"): Home Assistant itself sends none,
 * and 3dsearch.net's Cloudflare puts a challenge in front of requests without one — which may not show in a frame.
 */
(() => {
  const ORIGIN = 'https://3dsearch.net';
  const READY_TIMEOUT = 20000;
  const TXT = {
    de: ['Die Werkstatt lädt nicht.', 'In neuem Fenster öffnen'],
    en: ['The workshop does not load.', 'Open in a new window'],
    fr: ['L’atelier ne se charge pas.', 'Ouvrir dans une nouvelle fenêtre'],
    es: ['El taller no carga.', 'Abrir en una ventana nueva'],
    it: ['L’officina non si carica.', 'Apri in una nuova finestra'],
    nl: ['De werkplaats laadt niet.', 'Openen in een nieuw venster'],
  };

  class ThreeDSearchPanel extends HTMLElement {
    constructor() {
      super();
      this._loading = false;
      this._onMessage = this._onMessage.bind(this);
    }

    set hass(hass) {
      const first = !this._hass;
      this._hass = hass;
      if (this._menu) { this._menu.hass = hass; }
      if (first) this._render();
    }

    set narrow(narrow) {
      this._narrow = narrow;
      if (this._menu) this._menu.narrow = narrow;
    }

    set panel(panel) {
      this._panel = panel;
      if (this._hass && !this._frame) this._render();
    }

    connectedCallback() {
      window.addEventListener('message', this._onMessage);
      if (this._hass && this._panel && !this._frame) this._render();
    }

    disconnectedCallback() {
      window.removeEventListener('message', this._onMessage);
      clearTimeout(this._readyTimer);
    }

    _render() {
      if (!this._hass || !this._panel || this._frame) return;
      const root = this.shadowRoot || this.attachShadow({ mode: 'open' });
      root.innerHTML = `
        <style>
          /* Full window height on its own: Home Assistant gives custom panels no fixed height, so 100 % of the
             parent collapsed to zero and the frame was invisible (0.5.0b1/b2) */
          :host { display: block; position: relative; height: 100vh; height: 100dvh; overflow: hidden;
                  background: var(--primary-background-color); }
          .bar { position: absolute; top: 0; left: 0; right: 0; display: flex; align-items: center; gap: 4px; box-sizing: border-box;
                 height: calc(var(--header-height, 56px) + env(safe-area-inset-top, 0px)); padding: env(safe-area-inset-top, 0px) 12px 0 4px;
                 background: var(--app-header-background-color, var(--primary-color)); color: var(--app-header-text-color, #fff);
                 border-bottom: var(--app-header-border-bottom, none); }
          .title { font-size: 20px; font-weight: 400; margin-left: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
          .wrap { position: absolute; left: 0; right: 0; bottom: 0; top: calc(var(--header-height, 56px) + env(safe-area-inset-top, 0px)); }
          iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; display: block; background: var(--primary-background-color); }
          .msg { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; padding: 24px;
                 text-align: center; color: var(--secondary-text-color); font-size: 15px; background: var(--primary-background-color); }
          .msg[hidden] { display: none; }
          .msg a { color: var(--primary-color); }
        </style>
        <div class="bar"><ha-menu-button></ha-menu-button><div class="title"></div></div>
        <div class="wrap"><iframe title="3DSEARCH" allow="camera; clipboard-write; fullscreen" referrerpolicy="origin"></iframe><div class="msg">…</div></div>`;
      this._menu = root.querySelector('ha-menu-button');
      this._menu.hass = this._hass;
      this._menu.narrow = this._narrow;
      root.querySelector('.title').textContent = this._panel.title || '3DSEARCH';
      this._frame = root.querySelector('iframe');
      this._msg = root.querySelector('.msg');
      this._load('printers');
    }

    async _load(view) {
      if (this._loading) return;
      this._loading = true;
      this._msg.hidden = false;
      this._msg.textContent = '…';
      try {
        const r = await this._hass.callWS({ type: '3dsearch/embed', entry_id: this._panel.config.entry_id });
        if (!String(r.url).startsWith(ORIGIN + '/')) throw new Error('unexpected address');
        const lang = String((this._hass.locale && this._hass.locale.language) || this._hass.language || 'en').slice(0, 2);
        const theme = this._hass.themes && this._hass.themes.darkMode ? 'dark' : 'light';
        const v = /^[a-z0-9_]+$/.test(view || '') ? '&v=' + view : '';
        this._frame.src = `${r.url}?lang=${encodeURIComponent(lang)}&theme=${theme}#tok=${r.token}${v}`;
        this._msg.hidden = true;
        // The workshop reports "3dsearch-embed-ready" once it runs; without it the frame stays empty (blocked) → say so
        clearTimeout(this._readyTimer);
        this._readyTimer = setTimeout(() => {
          const [txt, link] = TXT[lang] || TXT.en;
          this._msg.innerHTML = `<div>${txt}<br><br><a href="${ORIGIN}/filament/" target="_blank" rel="noopener">${link}</a></div>`;
          this._msg.hidden = false;
        }, READY_TIMEOUT);
      } catch (err) {
        this._msg.textContent = '3DSEARCH: ' + ((err && (err.message || err.code)) || err);
        this._frame.removeAttribute('src');
      } finally {
        this._loading = false;
      }
    }

    _onMessage(e) {
      // Only our own frame, only from 3dsearch.net
      if (!this._frame || e.source !== this._frame.contentWindow || e.origin !== ORIGIN) return;
      const d = e.data || {};
      if (d.type === '3dsearch-embed-ready') { clearTimeout(this._readyTimer); this._msg.hidden = true; return; }
      if (d.type !== '3dsearch-embed-expired') return;
      // At most one new sign-in per minute: several requests of the old page can report the expiry at once, and a
      // sign-in that 3dsearch.net keeps refusing must not reload the frame in a loop
      const now = Date.now();
      if (this._renewed && now - this._renewed < 60000) return;
      this._renewed = now;
      this._load(typeof d.view === 'string' ? d.view : 'printers');
    }
  }

  if (!customElements.get('threedsearch-panel')) customElements.define('threedsearch-panel', ThreeDSearchPanel);
})();
