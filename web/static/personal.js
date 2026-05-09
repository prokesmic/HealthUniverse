/**
 * Health Universe — personal data store.
 *
 * All sensitive personal data (labs, wearable streams, genetic variants,
 * medical-record findings, n-of-1 protocol logs) lives EXCLUSIVELY in
 * the browser's localStorage. The server never sees PHI; it only ever
 * receives stateless lookup queries ("given lab X = 3.8, which edges
 * in the graph are relevant?").
 *
 * Schema is versioned. On a breaking change, bump SCHEMA and write a
 * migration; older data is kept and forward-migrated on first read.
 */

(function (global) {
  "use strict";

  const KEY = "hu_personal";
  const SCHEMA = 1;

  function _now() { return new Date().toISOString(); }
  function _today() { return new Date().toISOString().slice(0, 10); }
  function _rand() { return Math.random().toString(36).slice(2, 9); }

  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      if (!raw) return _empty();
      const parsed = JSON.parse(raw);
      return _migrate(parsed);
    } catch (_) {
      return _empty();
    }
  }

  function save(state) {
    state.updated_at = _now();
    localStorage.setItem(KEY, JSON.stringify(state));
    // Fire a custom event so any listening UI re-renders.
    document.dispatchEvent(new CustomEvent("hu-personal-changed", { detail: state }));
  }

  function _empty() {
    return {
      v: SCHEMA,
      labs: [],
      wearables: { rhr: [], sleep_hours: [], weight: [], hrv: [], steps: [], glucose: [] },
      genetics: [],
      records: [],
      protocols: [],
      created_at: _now(),
      updated_at: _now(),
    };
  }

  function _migrate(state) {
    if (!state || typeof state !== "object") return _empty();
    if (!state.v) state.v = 1;
    state.labs = state.labs || [];
    state.wearables = state.wearables || {};
    ["rhr", "sleep_hours", "weight", "hrv", "steps", "glucose"].forEach((k) => {
      state.wearables[k] = state.wearables[k] || [];
    });
    state.genetics = state.genetics || [];
    state.records = state.records || [];
    state.protocols = state.protocols || [];
    return state;
  }

  // ─── Labs ────────────────────────────────────────────────────────
  function addLab({ name, value, unit, date, source }) {
    const s = load();
    s.labs.push({
      id: _rand(),
      name: (name || "").trim(),
      value: Number(value),
      unit: (unit || "").trim(),
      date: date || _today(),
      source: (source || "manual").trim(),
      added_at: _now(),
    });
    save(s);
  }
  function deleteLab(id) {
    const s = load();
    s.labs = s.labs.filter((l) => l.id !== id);
    save(s);
  }

  // ─── Wearables ───────────────────────────────────────────────────
  function addWearablePoint(stream, { date, value }) {
    const s = load();
    if (!s.wearables[stream]) s.wearables[stream] = [];
    s.wearables[stream].push({ date: date || _today(), value: Number(value), id: _rand() });
    // Keep streams chronologically sorted, newest last.
    s.wearables[stream].sort((a, b) => a.date.localeCompare(b.date));
    save(s);
  }
  function deleteWearablePoint(stream, id) {
    const s = load();
    if (!s.wearables[stream]) return;
    s.wearables[stream] = s.wearables[stream].filter((p) => p.id !== id);
    save(s);
  }
  function bulkAddWearable(stream, points) {
    const s = load();
    if (!s.wearables[stream]) s.wearables[stream] = [];
    points.forEach((p) => {
      s.wearables[stream].push({ date: p.date, value: Number(p.value), id: _rand() });
    });
    s.wearables[stream].sort((a, b) => a.date.localeCompare(b.date));
    save(s);
  }

  // ─── Genetics ────────────────────────────────────────────────────
  function addVariant({ rsid, genotype, source }) {
    const s = load();
    rsid = (rsid || "").trim().toLowerCase();
    genotype = (genotype || "").trim().toUpperCase();
    if (!rsid.startsWith("rs")) return;
    // Replace existing variant for the same rsid rather than duplicate.
    s.genetics = s.genetics.filter((v) => v.rsid !== rsid);
    s.genetics.push({ id: _rand(), rsid, genotype, source: source || "manual", added_at: _now() });
    save(s);
  }
  function deleteVariant(id) {
    const s = load();
    s.genetics = s.genetics.filter((v) => v.id !== id);
    save(s);
  }
  function bulkAddVariants(rows) {
    const s = load();
    rows.forEach((r) => {
      const rsid = (r.rsid || "").trim().toLowerCase();
      const genotype = (r.genotype || "").trim().toUpperCase();
      if (!rsid.startsWith("rs")) return;
      s.genetics = s.genetics.filter((v) => v.rsid !== rsid);
      s.genetics.push({ id: _rand(), rsid, genotype, source: r.source || "23andMe", added_at: _now() });
    });
    save(s);
  }

  // ─── Records ─────────────────────────────────────────────────────
  function addRecord({ date, type, text, findings, label }) {
    const s = load();
    s.records.push({
      id: _rand(),
      date: date || _today(),
      type: (type || "note").trim(),
      label: (label || "").trim(),
      text: (text || "").trim(),
      findings: Array.isArray(findings) ? findings : [],
      added_at: _now(),
    });
    save(s);
  }
  function deleteRecord(id) {
    const s = load();
    s.records = s.records.filter((r) => r.id !== id);
    save(s);
  }

  // ─── Protocols (n-of-1) ──────────────────────────────────────────
  function addProtocol({ factor_slug, factor_name, outcome_slug, outcome_name, started_at, duration_days, baseline_note }) {
    const s = load();
    const start = started_at || _today();
    const dur = Number(duration_days) || 28;
    const ends = new Date(start);
    ends.setDate(ends.getDate() + dur);
    s.protocols.push({
      id: _rand(),
      factor_slug, factor_name, outcome_slug, outcome_name,
      started_at: start,
      ends_at: ends.toISOString().slice(0, 10),
      baseline_note: baseline_note || "",
      logs: [],
      added_at: _now(),
    });
    save(s);
  }
  function logProtocol(id, { date, score, note }) {
    const s = load();
    const p = s.protocols.find((x) => x.id === id);
    if (!p) return;
    p.logs.push({ id: _rand(), date: date || _today(), score: Number(score), note: (note || "").trim() });
    p.logs.sort((a, b) => a.date.localeCompare(b.date));
    save(s);
  }
  function deleteProtocol(id) {
    const s = load();
    s.protocols = s.protocols.filter((p) => p.id !== id);
    save(s);
  }

  // ─── Reset / export ──────────────────────────────────────────────
  function exportJSON() {
    const s = load();
    return JSON.stringify(s, null, 2);
  }
  function importJSON(text) {
    try {
      const parsed = JSON.parse(text);
      const migrated = _migrate(parsed);
      save(migrated);
      return true;
    } catch (e) {
      return false;
    }
  }
  function clearAll() {
    localStorage.removeItem(KEY);
    document.dispatchEvent(new CustomEvent("hu-personal-changed", { detail: _empty() }));
  }

  // ─── Counts (used to compose the hub's headline) ─────────────────
  function counts() {
    const s = load();
    const wcounts = Object.values(s.wearables).reduce((a, b) => a + b.length, 0);
    return {
      labs: s.labs.length,
      wearable_points: wcounts,
      wearable_streams: Object.keys(s.wearables).filter(
        (k) => (s.wearables[k] || []).length > 0
      ).length,
      genetics: s.genetics.length,
      records: s.records.length,
      protocols: s.protocols.length,
    };
  }

  global.HUPersonal = {
    load, save, counts,
    addLab, deleteLab,
    addWearablePoint, deleteWearablePoint, bulkAddWearable,
    addVariant, deleteVariant, bulkAddVariants,
    addRecord, deleteRecord,
    addProtocol, logProtocol, deleteProtocol,
    exportJSON, importJSON, clearAll,
  };
})(window);
