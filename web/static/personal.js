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
      // Recommendations the system has surfaced to the user. Each row is
      // logged with timestamp + status so we can close the loop later
      // ('I told you to try X 8 weeks ago — here's whether it worked').
      recommendations: [],
      // Upcoming clinical visits — input for /me/checkup pre-visit prep.
      visits: [],
      // Email opt-in for proactive emails (Sunday briefing, protocol
      // reminders). Set on /me/briefing's 'subscribe' button.
      email: null,
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
    state.recommendations = state.recommendations || [];
    state.visits = state.visits || [];
    if (state.email === undefined) state.email = null;
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

  // ─── Recommendations log (loop closure) ─────────────────────────
  // Local-only for anonymous users; mirrored to Supabase via the
  // /api/me/recommendation endpoint when signed in (server silently
  // no-ops if no session cookie).
  function _mirrorRecommendation(payload) {
    try {
      fetch("/api/me/recommendation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).catch(() => {});
    } catch (_) {}
  }
  function _mirrorClose(payload) {
    try {
      fetch("/api/me/recommendation/close", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).catch(() => {});
    } catch (_) {}
  }
  function addRecommendation({ edge_id, edge_label, source, target_metric, baseline_value }) {
    const s = load();
    const key = `${source || "system"}:${edge_id}`;
    // Don't double-log: same source + edge in last 14 days is a no-op.
    const recent = s.recommendations.find((r) =>
      `${r.source}:${r.edge_id}` === key &&
      (Date.now() - new Date(r.suggested_at).getTime()) < 14 * 86400000);
    if (recent) return;
    s.recommendations.push({
      id: _rand(),
      edge_id, edge_label,
      source: source || "system",
      target_metric: target_metric || null,
      baseline_value: baseline_value != null ? Number(baseline_value) : null,
      suggested_at: _now(),
      status: "open",
      closed_at: null,
      verdict: null,
      followup_value: null,
    });
    save(s);
    // Best-effort server mirror for signed-in users.
    _mirrorRecommendation({ edge_id, edge_label, source: source || "system" });
  }
  function closeRecommendation(id, { verdict, followup_value }) {
    const s = load();
    const r = s.recommendations.find((x) => x.id === id);
    if (!r) return;
    r.status = "closed";
    r.closed_at = _now();
    r.verdict = verdict || "uncertain";
    if (followup_value != null) r.followup_value = Number(followup_value);
    save(s);
    _mirrorClose({ edge_id: r.edge_id, verdict: r.verdict });
  }
  function deleteRecommendation(id) {
    const s = load();
    s.recommendations = s.recommendations.filter((r) => r.id !== id);
    save(s);
  }

  // ─── Visits / appointments ──────────────────────────────────────
  function addVisit({ date, clinician, notes }) {
    const s = load();
    s.visits.push({
      id: _rand(),
      date: date || _today(),
      clinician: (clinician || "").trim(),
      notes: (notes || "").trim(),
      added_at: _now(),
    });
    s.visits.sort((a, b) => a.date.localeCompare(b.date));
    save(s);
  }
  function deleteVisit(id) {
    const s = load();
    s.visits = s.visits.filter((v) => v.id !== id);
    save(s);
  }

  // ─── Email opt-in ───────────────────────────────────────────────
  function setEmail(email) {
    const s = load();
    s.email = (email || "").trim().toLowerCase() || null;
    save(s);
  }

  // ─── Anomaly detection on wearable streams ──────────────────────
  // For each stream with ≥14 points, compute a z-score of the last 7
  // days vs the prior 60 (or however much we have). Flag anomalies
  // with |z| ≥ 1.5 — strong enough to be worth surfacing without
  // being so trigger-happy we cry wolf.
  const _BETTER_DIRECTION = {
    rhr: "down", sleep_hours: "up", weight: null,
    hrv: "up", steps: "up", glucose: "down",
  };
  function detectAnomalies(threshold = 1.5) {
    const s = load();
    const out = [];
    Object.entries(s.wearables || {}).forEach(([stream, pts]) => {
      if (!Array.isArray(pts) || pts.length < 10) return;
      const sorted = [...pts].sort((a, b) => a.date.localeCompare(b.date));
      const recent = sorted.slice(-7);
      const baseline = sorted.slice(0, -7).slice(-60);
      if (recent.length < 4 || baseline.length < 5) return;
      const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
      const stdev = (a, m) => Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / a.length) || 1;
      const bvals = baseline.map((p) => p.value);
      const rvals = recent.map((p) => p.value);
      const bm = mean(bvals);
      const bs = stdev(bvals, bm);
      const rm = mean(rvals);
      const z = (rm - bm) / bs;
      if (Math.abs(z) >= threshold) {
        const better = _BETTER_DIRECTION[stream];
        let direction = z > 0 ? "up" : "down";
        let isBad = better && direction !== better;
        out.push({
          stream, z: Number(z.toFixed(2)),
          recent_mean: Number(rm.toFixed(2)), baseline_mean: Number(bm.toFixed(2)),
          delta: Number((rm - bm).toFixed(2)),
          n_recent: recent.length, n_baseline: baseline.length,
          direction, severity: Math.abs(z) >= 2.5 ? "high" : "moderate",
          is_bad: isBad,
        });
      }
    });
    return out.sort((a, b) => Math.abs(b.z) - Math.abs(a.z));
  }

  // ─── Cross-stream correlation (weekly) ──────────────────────────
  // Daily-aligned Pearson between every pair of wearable streams that
  // have ≥14 overlapping daily points. Returns the strongest 3 by |r|.
  function computeCorrelations() {
    const s = load();
    const dailyMap = {}; // stream → date → averaged value
    Object.entries(s.wearables || {}).forEach(([stream, pts]) => {
      const m = {};
      (pts || []).forEach((p) => {
        const d = p.date;
        m[d] = (m[d] != null) ? (m[d] + p.value) / 2 : p.value;
      });
      if (Object.keys(m).length >= 14) dailyMap[stream] = m;
    });
    const streams = Object.keys(dailyMap);
    const pairs = [];
    for (let i = 0; i < streams.length; i++) {
      for (let j = i + 1; j < streams.length; j++) {
        const a = dailyMap[streams[i]], b = dailyMap[streams[j]];
        const dates = Object.keys(a).filter((d) => d in b).sort();
        if (dates.length < 14) continue;
        const xs = dates.map((d) => a[d]);
        const ys = dates.map((d) => b[d]);
        const n = xs.length;
        const mean = (arr) => arr.reduce((x, y) => x + y, 0) / n;
        const mx = mean(xs), my = mean(ys);
        let num = 0, dx = 0, dy = 0;
        for (let k = 0; k < n; k++) {
          num += (xs[k] - mx) * (ys[k] - my);
          dx += (xs[k] - mx) ** 2;
          dy += (ys[k] - my) ** 2;
        }
        const denom = Math.sqrt(dx * dy) || 1;
        const r = num / denom;
        if (Math.abs(r) >= 0.35) {
          pairs.push({
            a: streams[i], b: streams[j], r: Number(r.toFixed(2)),
            n, sign: r > 0 ? "co_move" : "anti_move",
          });
        }
      }
    }
    return pairs.sort((a, b) => Math.abs(b.r) - Math.abs(a.r)).slice(0, 5);
  }

  // ─── Protocol nudge state ───────────────────────────────────────
  // Returns a list of protocols where the user hasn't logged in 3+
  // days, or where the duration has elapsed and we should offer to
  // close out and compute the personal-effect estimate.
  function protocolNudges() {
    const s = load();
    const today = _today();
    const out = [];
    (s.protocols || []).forEach((p) => {
      const lastLog = p.logs && p.logs.length ? p.logs[p.logs.length - 1].date : p.started_at;
      const daysSinceLog = (new Date(today) - new Date(lastLog)) / 86400000;
      const isComplete = today >= p.ends_at;
      const isStale = daysSinceLog >= 3 && !isComplete;
      if (isComplete && p.logs.length >= 4) {
        out.push({ id: p.id, kind: "ready_to_close", protocol: p });
      } else if (isStale) {
        out.push({ id: p.id, kind: "stale", days_since_log: Math.floor(daysSinceLog), protocol: p });
      }
    });
    return out;
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
    addRecommendation, closeRecommendation, deleteRecommendation,
    addVisit, deleteVisit,
    setEmail,
    detectAnomalies, computeCorrelations, protocolNudges,
    exportJSON, importJSON, clearAll,
  };
})(window);
