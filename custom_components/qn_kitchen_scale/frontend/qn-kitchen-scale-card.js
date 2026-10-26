// Lovelace card for QN Kitchen Scale: live weight, scale status and the latest measurements.
// Served by the integration itself (see __init__.py), so no separate resource is needed.

const DOMAIN = "qn_kitchen_scale";
const CARD_TYPE = "qn-kitchen-scale-card";
// Height of one history row in px; the card shows as many rows as fit.
const ROW = 24;
const DEFAULT_MAX_ITEMS = 5;
// Session headers take a row each; below this many rows the list stays flat.
const MIN_ROWS_FOR_SESSIONS = 3;

const STRINGS = {
  en: {
    name: "QN Kitchen Scale",
    description: "Live weight, scale status and the latest measurements.",
    stable: "Stable",
    tare: "Tare",
    connected: "Connected",
    disconnected: "Disconnected",
    asleep: "Scale asleep",
    battery: "Battery {0} %",
    empty: "No measurements yet",
    clear: "Clear",
    clearAll: "Clear measurements",
    keep: "Keep measurements",
    notFound: "No QN Kitchen Scale found",
    entity: "Weight sensor",
    maxItems: "Measurements shown outside the sections grid",
  },
  ru: {
    name: "Кухонные весы QN",
    description: "Текущий вес, состояние весов и последние измерения.",
    stable: "Стабильно",
    tare: "Тара",
    connected: "Подключены",
    disconnected: "Не подключены",
    asleep: "Весы спят",
    battery: "Батарея {0} %",
    empty: "Измерений пока нет",
    clear: "Очистить",
    clearAll: "Очистить измерения",
    keep: "Оставить измерения",
    notFound: "Весы QN не найдены",
    entity: "Датчик веса",
    maxItems: "Сколько измерений показывать вне сетки секций",
  },
};

const UNIT_LABELS = { ml: "ml", ml_milk: "ml milk", oz: "oz", lb_oz: "lb:oz" };

const TRASH = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-12M9 7V4h6v3"/></svg>`;

const sheet = new CSSStyleSheet();
sheet.replaceSync(`
:host {
  display: block;
  height: 100%;
  container-type: inline-size;
  --_ok: var(--success-color, #43a047);
  --_danger: var(--error-color, #db4437);
  --_accent: var(--primary-color, #03a9f4);
  --_sec: var(--secondary-text-color, #727272);
  --_divider: var(--divider-color, rgba(0, 0, 0, 0.12));
}
ha-card {
  height: 100%;
  box-sizing: border-box;
  padding: 6px 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-variant-numeric: tabular-nums;
}
[hidden] { display: none !important; }
svg { fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

.now { display: flex; align-items: center; gap: 8px; min-height: 44px; flex-shrink: 0; }
.weight { display: flex; align-items: baseline; gap: 3px; white-space: nowrap; flex-shrink: 0; }
/* Tags that do not fit wrap onto a hidden second line, so they drop out whole, last first. */
.tags { display: flex; flex-wrap: wrap; gap: 6px; height: 20px; overflow: hidden; min-width: 0; flex: 0 1 auto; }
.icon { flex-shrink: 0; }
.value { font-size: 36px; line-height: 40px; letter-spacing: -0.5px; }
.unit { font-size: 16px; color: var(--_sec); }
:host([asleep]) .value, :host([asleep]) .unit { color: var(--disabled-text-color, var(--_sec)); }
.tag {
  height: 20px; padding: 0 8px; border-radius: 10px; box-sizing: border-box;
  display: inline-flex; align-items: center; white-space: nowrap;
  font-size: 11px; font-weight: 500;
}
.stable { background: color-mix(in srgb, var(--_ok) 15%, transparent); color: var(--_ok); }
.tare, .shown-unit { border: 1px solid var(--_sec); color: var(--_sec); }
.tare { text-transform: uppercase; letter-spacing: 0.5px; font-size: 10px; }
.spacer { flex-grow: 1; }
.icon { display: inline-flex; color: var(--_sec); }
.icon svg { width: 18px; height: 18px; }
.link[data-on] { color: var(--_accent); }
.battery svg { width: 26px; height: 14px; stroke: none; }
.battery .shell { fill: none; stroke: var(--_sec); stroke-width: 1.5; }
.battery .tip { fill: var(--_sec); }
.battery .level { fill: var(--_ok); }
.battery[data-low] .level { fill: var(--_danger); }

.history { position: relative; flex: 1 1 auto; min-height: 0; border-top: 1px solid var(--_divider); padding-top: 4px; }
:host([no-history]) .history { display: none; }
ol { list-style: none; margin: 0; padding: 0 36px 0 0; }
li { display: grid; grid-template-columns: 80px minmax(0, 1fr); align-items: center; gap: 8px; height: ${ROW}px; font-size: 13px; }
/* When a scale session started: a small caption with a rule running to the right. */
.s { grid-template-columns: auto minmax(0, 1fr); font-size: 10px; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase; color: var(--_sec); }
.s::after { content: ""; height: 1px; background: var(--_divider); }
.w { font-weight: 500; }
.d { font-size: 12px; color: var(--_sec); }
.empty { margin: 0; display: flex; align-items: center; justify-content: center; font-size: 13px; color: var(--_sec); }
.actions { position: absolute; top: 2px; right: -6px; }
button {
  font: inherit; cursor: pointer; border: none; background: transparent; color: var(--_sec);
  display: inline-flex; align-items: center; justify-content: center; gap: 4px;
}
button:focus-visible { outline: 2px solid var(--_accent); outline-offset: 1px; }
.clear, .keep { width: 36px; height: 36px; border-radius: 18px; }
.clear svg { width: 18px; height: 18px; }
.keep svg { width: 16px; height: 16px; }
.confirm {
  display: flex; align-items: center; gap: 4px; padding: 2px; border-radius: 20px;
  background: var(--ha-card-background, var(--card-background-color, #fff));
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
}
.do {
  height: 32px; padding: 0 12px; border-radius: 16px; background: var(--_danger); color: #fff;
  font-size: 12px; font-weight: 500;
}
.do svg { width: 14px; height: 14px; }
.notice { margin: 0; padding: 12px 4px; color: var(--_sec); }
:host(:not([missing])) .notice, :host([missing]) .now, :host([missing]) .history { display: none; }

/* Narrow cells: shrink the number, then keep only the weight. */
@container (max-width: 300px) {
  .value { font-size: 24px; line-height: 32px; letter-spacing: 0; }
  .unit { font-size: 13px; }
  ha-card { padding: 6px 10px; }
  .now { min-height: 40px; gap: 5px; }
  .tags { height: 18px; gap: 4px; }
  .tag { height: 18px; padding: 0 6px; font-size: 10px; }
  .icon svg { width: 16px; height: 16px; }
  /* A live weight already says the scale is connected; keep the room for tags. */
  .link[data-on] { display: none; }
  .battery svg { width: 22px; height: 12px; }
  li { grid-template-columns: 76px minmax(0, 1fr); gap: 6px; }
}
@container (max-width: 180px) {
  .tags, .icon, .spacer, .d { display: none; }
  .now { justify-content: center; }
  li { grid-template-columns: 1fr; }
  .s { display: none; }
}
`);

const template = document.createElement("template");
template.innerHTML = `
<ha-card>
  <div class="now">
    <p class="weight" style="margin:0"><span class="value">—</span><span class="unit">g</span></p>
    <span class="tags">
      <span class="tag stable" hidden></span>
      <span class="tag tare" hidden></span>
      <span class="tag shown-unit" hidden></span>
    </span>
    <span class="spacer"></span>
    <span class="icon sleep" role="img" hidden><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/></svg></span>
    <span class="icon link" role="img"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10-5 5V2l5 5L7 17"/><path class="cross" d="M3 3l18 18"/></svg></span>
    <span class="icon battery" role="img" hidden><svg viewBox="0 0 26 14" aria-hidden="true"><rect class="shell" x="0.75" y="0.75" width="21.5" height="12.5" rx="2.5"/><rect class="tip" x="23.5" y="4.5" width="2" height="5" rx="1"/><rect class="level" x="3" y="3" width="17" height="8" rx="1"/></svg></span>
  </div>
  <section class="history">
    <ol></ol>
    <p class="empty" hidden></p>
    <div class="actions">
      <button type="button" class="clear">${TRASH}</button>
      <div class="confirm" hidden>
        <button type="button" class="keep"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
        <button type="button" class="do">${TRASH}<span></span></button>
      </div>
    </div>
  </section>
  <p class="notice"></p>
</ha-card>
`;

// The scale's entities, found through the device of the weight sensor.
function resolveEntities(hass, config) {
  const registry = hass.entities || {};
  let weight = config.entity;
  if (!weight) {
    const found = Object.values(registry).find(
      (e) => e.platform === DOMAIN && e.translation_key === "weight",
    );
    weight = found && found.entity_id;
  }
  if (!weight) return null;
  const device = registry[weight] && registry[weight].device_id;
  const byKey = {};
  if (device) {
    for (const e of Object.values(registry)) {
      if (e.device_id === device && e.platform === DOMAIN && e.translation_key) {
        byKey[e.translation_key] = e.entity_id;
      }
    }
  }
  // Without the registry, fall back to the default entity ids next to the weight sensor.
  const base = weight.replace(/^sensor\./, "").replace(/_weight$/, "");
  return {
    weight,
    last: config.measurements_entity || byKey.last_measurement || `sensor.${base}_last_measurement`,
    battery: config.battery_entity || byKey.battery || `sensor.${base}_battery`,
    connected: config.connected_entity || byKey.connected || `binary_sensor.${base}_connected`,
  };
}

// When the session of items[i] started: the time of its oldest measurement in the (newest-first) list.
function sessionStart(items, i) {
  let j = i;
  while (j + 1 < items.length && items[j + 1].session === items[i].session) j += 1;
  return items[j].at;
}

function startOfDay(d) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function strings(hass) {
  const lang = ((hass && hass.locale && hass.locale.language) || "en").split("-")[0];
  return STRINGS[lang] || STRINGS.en;
}

class QnKitchenScaleCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.adoptedStyleSheets = [sheet];
    this.shadowRoot.append(template.content.cloneNode(true));
    const $ = (s) => this.shadowRoot.querySelector(s);
    this._el = {
      card: $("ha-card"),
      now: $(".now"),
      value: $(".value"),
      unit: $(".unit"),
      stable: $(".stable"),
      tare: $(".tare"),
      shownUnit: $(".shown-unit"),
      sleep: $(".sleep"),
      link: $(".link"),
      cross: $(".cross"),
      battery: $(".battery"),
      level: $(".level"),
      list: $("ol"),
      empty: $(".empty"),
      clear: $(".clear"),
      confirm: $(".confirm"),
      keep: $(".keep"),
      doClear: $(".do"),
      doLabel: $(".do span"),
      notice: $(".notice"),
    };
    this._confirming = false;
    this._rows = DEFAULT_MAX_ITEMS;
    this._el.clear.addEventListener("click", () => this._setConfirming(true, this._el.keep));
    this._el.keep.addEventListener("click", () => this._setConfirming(false, this._el.clear));
    this._el.doClear.addEventListener("click", () => {
      this._hass.callService(DOMAIN, "clear_measurements", {});
      this._setConfirming(false, null);
    });
    this._resize = new ResizeObserver(() => this._fitRows());
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "entity", selector: { entity: { integration: DOMAIN, domain: "sensor" } } },
        { name: "max_items", selector: { number: { min: 0, max: 50, mode: "box" } } },
      ],
      computeLabel: (schema, hass) =>
        schema.name === "entity" ? strings(hass).entity : strings(hass).maxItems,
    };
  }

  static getStubConfig(hass) {
    const found = resolveEntities(hass, {});
    return found ? { entity: found.weight } : {};
  }

  setConfig(config) {
    this._config = { ...config };
    this._rows = this._config.max_items ?? DEFAULT_MAX_ITEMS;
    this._seen = null;
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._config) this._render();
  }

  getCardSize() {
    return 1 + Math.ceil((this._rows * ROW) / 50);
  }

  getGridOptions() {
    return { columns: 12, rows: 3, min_columns: 3, min_rows: 1 };
  }

  connectedCallback() {
    this._resize.observe(this._el.card);
  }

  disconnectedCallback() {
    this._resize.disconnect();
  }

  _setConfirming(on, focus) {
    this._confirming = on;
    this._el.clear.hidden = on;
    this._el.confirm.hidden = !on;
    if (focus) focus.focus();
  }

  // Rows that fit under the weight line. Outside a fixed-height grid cell the card grows with its
  // rows, so the count stays at max_items; inside one it follows the cell.
  _fitRows() {
    const card = this._el.card;
    const style = getComputedStyle(card);
    const inner = card.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
    const free = inner - this._el.now.offsetHeight - 5;
    const rows = Math.max(0, Math.floor(free / ROW));
    if (rows !== this._rows) {
      this._rows = rows;
      this._renderHistory();
    }
  }

  _render() {
    const ids = resolveEntities(this._hass, this._config);
    const t = strings(this._hass);
    this.toggleAttribute("missing", !ids);
    if (!ids) {
      this._el.notice.textContent = t.notFound;
      return;
    }
    const states = this._hass.states;
    const seen = [ids.weight, ids.last, ids.battery, ids.connected].map((id) => states[id]);
    if (this._seen && seen.every((s, i) => s === this._seen[i]) && this._lang === t) return;
    this._seen = seen;
    this._lang = t;
    this._ids = ids;
    const [weight, , battery, connected] = seen;
    const el = this._el;

    const awake = weight && !["unavailable", "unknown"].includes(weight.state);
    this.toggleAttribute("asleep", !awake);
    el.value.textContent = awake ? this._grams(Number(weight.state)) : "—";
    const attrs = (weight && weight.attributes) || {};
    el.stable.textContent = t.stable;
    el.stable.hidden = !(awake && attrs.stable);
    el.tare.textContent = t.tare;
    el.tare.hidden = !(awake && attrs.tare);
    const shown = UNIT_LABELS[attrs.display_unit];
    el.shownUnit.textContent = shown || "";
    el.shownUnit.hidden = !(awake && shown);
    el.sleep.hidden = awake;
    el.sleep.setAttribute("aria-label", t.asleep);

    const isOn = connected && connected.state === "on";
    el.link.toggleAttribute("data-on", Boolean(isOn));
    el.cross.style.display = isOn ? "none" : "";
    el.link.setAttribute("aria-label", isOn ? t.connected : t.disconnected);

    const level = battery ? Number(battery.state) : NaN;
    el.battery.hidden = Number.isNaN(level);
    if (!Number.isNaN(level)) {
      el.level.setAttribute("width", String(Math.max(1, (17 * Math.min(level, 100)) / 100)));
      el.battery.toggleAttribute("data-low", level < 20);
      el.battery.setAttribute("aria-label", t.battery.replace("{0}", level));
    }

    el.clear.setAttribute("aria-label", t.clearAll);
    el.keep.setAttribute("aria-label", t.keep);
    el.doLabel.textContent = t.clear;
    el.empty.textContent = t.empty;
    this._renderHistory();
  }

  _renderHistory() {
    if (!this._ids) return;
    const el = this._el;
    const last = this._hass.states[this._ids.last];
    const items = (last && last.attributes.measurements) || [];
    this.toggleAttribute("no-history", this._rows === 0);
    const lang = (this._hass.locale && this._hass.locale.language) || "en";
    const rows = [];
    // Each scale session (switch-on) opens with the time it started, so the measurements just made
    // stand apart from older ones. Too few rows for that: the plain list, as before.
    const headers = this._rows >= MIN_ROWS_FOR_SESSIONS;
    for (const [i, m] of items.entries()) {
      if (rows.length >= this._rows) break;
      if (headers && (i === 0 || m.session !== items[i - 1].session)) {
        // A header needs a measurement under it; the last row goes to the measurement instead.
        if (rows.length + 1 >= this._rows) break;
        const h = document.createElement("li");
        h.className = "s";
        h.append(Object.assign(document.createElement("span"), { textContent: this._when(sessionStart(items, i)) }));
        rows.push(h);
      }
      const li = document.createElement("li");
      li.title = new Date(m.at).toLocaleTimeString(lang);
      const w = Object.assign(document.createElement("span"), {
        className: "w",
        textContent: `${this._grams(m.weight_g)} g`,
      });
      const d = Object.assign(document.createElement("span"), {
        className: "d",
        textContent: m.delta_g == null ? "" : `${this._signed(m.delta_g)} g`,
      });
      li.append(w, d);
      rows.push(li);
    }
    // Both keep the full row height even when half empty, so the card does not shrink and lose
    // rows before new measurements arrive.
    el.list.replaceChildren(...rows);
    el.list.hidden = rows.length === 0;
    el.list.style.minHeight = `${this._rows * ROW}px`;
    el.empty.hidden = items.length > 0;
    el.empty.style.height = `${this._rows * ROW}px`;
    el.clear.disabled = items.length === 0;
    el.clear.parentElement.hidden = items.length === 0 && !this._confirming;
  }

  // Grams as the scale shows them: 0.1 g steps below 1 kg, whole grams above.
  _grams(value) {
    const digits = Math.abs(value) >= 1000 ? 0 : 1;
    const lang = (this._hass.locale && this._hass.locale.language) || "en";
    return new Intl.NumberFormat(lang, {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(value);
  }

  // "Today, 14:32", "Yesterday, 19:05", then "20 Oct, 08:40" (with the year once it differs).
  _when(iso) {
    const at = new Date(iso);
    const now = new Date();
    const lang = (this._hass.locale && this._hass.locale.language) || "en";
    const hour12 = this._hass.locale && this._hass.locale.time_format === "12" ? true
      : this._hass.locale && this._hass.locale.time_format === "24" ? false : undefined;
    const time = at.toLocaleTimeString(lang, { hour: "numeric", minute: "2-digit", hour12 });
    const days = Math.round((startOfDay(at) - startOfDay(now)) / 86400000);
    let day;
    if (days === 0 || days === -1) {
      day = new Intl.RelativeTimeFormat(lang, { numeric: "auto" }).format(days, "day");
      day = day.charAt(0).toUpperCase() + day.slice(1);
    } else {
      const sameYear = at.getFullYear() === now.getFullYear();
      day = at.toLocaleDateString(lang, { day: "numeric", month: "short", year: sameYear ? undefined : "numeric" });
    }
    return `${day}, ${time}`;
  }

  _signed(value) {
    const text = this._grams(Math.abs(value));
    return value < 0 ? `−${text}` : `+${text}`;
  }
}

if (!customElements.get(CARD_TYPE)) {
  customElements.define(CARD_TYPE, QnKitchenScaleCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: CARD_TYPE,
    name: STRINGS.en.name,
    description: STRINGS.en.description,
    preview: true,
    documentationURL: "https://github.com/jaxer/ha-qn-kitchen-scale",
  });
}
