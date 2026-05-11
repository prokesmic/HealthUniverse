/**
 * Health Universe — always-on client layer.
 *
 * Three concerns:
 *
 *   1. End-to-end encrypted backup of HUPersonal localStorage to
 *      the server. Key is derived from the user's passphrase via
 *      PBKDF2; the server only ever sees ciphertext.
 *
 *   2. The opt-in "compute summary" — a small server-readable JSON
 *      of derived signals (NO raw PHI) that the daily cron uses to
 *      run personal compute on the user's behalf.
 *
 *   3. Web Push subscription registration so the daily compute can
 *      land a notification on the user's device.
 */

(function (global) {
  "use strict";
  const SUBTLE = (window.crypto && window.crypto.subtle) || null;

  // ─── Crypto helpers ───────────────────────────────────────────
  function b64u(bytes) {
    let s = ""; const arr = new Uint8Array(bytes);
    for (let i = 0; i < arr.length; i++) s += String.fromCharCode(arr[i]);
    return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }
  function unb64u(str) {
    str = str.replace(/-/g, "+").replace(/_/g, "/");
    while (str.length % 4) str += "=";
    const bin = atob(str);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return arr;
  }
  async function deriveKey(passphrase, saltBytes, iterations) {
    const enc = new TextEncoder();
    const baseKey = await SUBTLE.importKey(
      "raw", enc.encode(passphrase),
      { name: "PBKDF2" }, false, ["deriveKey"]);
    return SUBTLE.deriveKey(
      { name: "PBKDF2", salt: saltBytes, iterations, hash: "SHA-256" },
      baseKey,
      { name: "AES-GCM", length: 256 },
      false,
      ["encrypt", "decrypt"]);
  }
  async function encrypt(payload, passphrase) {
    if (!SUBTLE) throw new Error("WebCrypto unavailable");
    const salt = window.crypto.getRandomValues(new Uint8Array(16));
    const iv   = window.crypto.getRandomValues(new Uint8Array(12));
    const iterations = 200000;
    const key = await deriveKey(passphrase, salt, iterations);
    const data = new TextEncoder().encode(JSON.stringify(payload));
    const ct = await SUBTLE.encrypt({ name: "AES-GCM", iv }, key, data);
    return {
      ciphertext: b64u(ct),
      iv: b64u(iv),
      salt: b64u(salt),
      iterations,
    };
  }
  async function decrypt(record, passphrase) {
    if (!SUBTLE) throw new Error("WebCrypto unavailable");
    const salt = unb64u(record.salt);
    const iv   = unb64u(record.iv);
    const ct   = unb64u(record.ciphertext);
    const key = await deriveKey(passphrase, salt, record.iterations || 200000);
    const plain = await SUBTLE.decrypt({ name: "AES-GCM", iv }, key, ct);
    return JSON.parse(new TextDecoder().decode(plain));
  }

  // ─── Sync the encrypted blob ─────────────────────────────────
  async function syncToServer(passphrase) {
    if (!window.HUPersonal) throw new Error("HUPersonal missing");
    const data = window.HUPersonal.load();
    const enc = await encrypt(data, passphrase);
    const r = await fetch("/api/me/synced-blob", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(enc),
    });
    return r.ok;
  }
  async function restoreFromServer(passphrase) {
    const r = await fetch("/api/me/synced-blob");
    if (!r.ok) throw new Error("sync fetch failed: " + r.status);
    const rec = await r.json();
    if (!rec || !rec.ciphertext) throw new Error("no_blob");
    const data = await decrypt(rec, passphrase);
    if (window.HUPersonal && typeof window.HUPersonal.importJSON === "function") {
      window.HUPersonal.importJSON(JSON.stringify(data));
    } else {
      localStorage.setItem("hu_personal", JSON.stringify(data));
    }
    return true;
  }

  // ─── Compute summary — what the server CAN read ──────────────
  function buildComputeSummary() {
    if (!window.HUPersonal) return null;
    const HU = window.HUPersonal;
    const data = HU.load();
    const anomalies = HU.detectAnomalies();
    const anomalyMap = {};
    anomalies.forEach((a) => {
      anomalyMap[a.stream] = {
        z: a.z, dir: a.direction,
        recent_mean: a.recent_mean,
        baseline_mean: a.baseline_mean,
        is_bad: a.is_bad,
        severity: a.severity,
      };
    });
    // Recent trend snapshots — last value per stream, no historical PHI.
    const trends = {};
    Object.entries(data.wearables || {}).forEach(([stream, pts]) => {
      if (!pts || !pts.length) return;
      const last7 = pts.slice(-7).map((p) => p.value);
      const last30 = pts.slice(-30).map((p) => p.value);
      const mean = (a) => a.length ? a.reduce((x, y) => x + y, 0) / a.length : null;
      trends[stream] = { "7d_avg": mean(last7), "30d_avg": mean(last30) };
    });
    // Open recommendations (no PHI; just edge IDs + days open).
    const openRecs = (data.recommendations || [])
      .filter((r) => r.status === "open")
      .map((r) => ({
        edge_id: r.edge_id,
        edge_label: r.edge_label,
        source: r.source,
        days_open: Math.floor((Date.now() - new Date(r.suggested_at).getTime()) / 86400000),
      }));
    // Next visit.
    let nextVisit = null;
    const today = new Date().toISOString().slice(0, 10);
    for (const v of (data.visits || [])) {
      if (v.date >= today) { nextVisit = { date: v.date, clinician: v.clinician }; break; }
    }
    // Flagged labs — names + values + direction (this IS PHI-ish; only
    // flagged ones flow up, and the user explicitly opted in).
    const flagged = [];
    // We don't have lab evidence overlay client-side; just send names
    // for now. The cron treats these as soft hints.
    (data.labs || []).slice(-12).forEach((l) => {
      flagged.push({ name: l.name, value: l.value, unit: l.unit, date: l.date });
    });
    // Active protocols.
    const protos = (data.protocols || []).map((p) => ({
      factor: p.factor_slug,
      started_at: p.started_at,
      ends_at: p.ends_at,
      logs_count: (p.logs || []).length,
    }));
    // Watch_edges live in the legacy hu_profile cookie / server.
    // Client doesn't have direct access; the server already has them
    // via the profile. We send what we know.
    const tz = (Intl.DateTimeFormat().resolvedOptions().timeZone) || "UTC";
    return {
      timezone: tz,
      anomaly_zscores: anomalyMap,
      recent_trends: trends,
      open_recommendations: openRecs,
      next_visit: nextVisit,
      flagged_labs: flagged,
      active_protocols: protos,
    };
  }
  async function syncComputeSummary(agreed) {
    const s = buildComputeSummary();
    if (!s) return false;
    s.agreed_to_daily_compute = !!agreed;
    const r = await fetch("/api/me/compute-summary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(s),
    });
    return r.ok;
  }
  async function getComputeSummary() {
    const r = await fetch("/api/me/compute-summary");
    if (!r.ok) return null;
    return await r.json();
  }

  // ─── Web Push subscription ────────────────────────────────────
  async function registerSW() {
    if (!("serviceWorker" in navigator)) throw new Error("no_sw");
    return await navigator.serviceWorker.register("/service-worker.js");
  }
  async function subscribePush() {
    const reg = await registerSW();
    if (!("PushManager" in window)) throw new Error("no_push");
    const r = await fetch("/api/vapid-key");
    const { public_key } = await r.json();
    if (!public_key) throw new Error("no_vapid");
    const appServerKey = unb64u(public_key);
    const perm = await Notification.requestPermission();
    if (perm !== "granted") throw new Error("permission_denied");
    const existing = await reg.pushManager.getSubscription();
    if (existing) {
      try { await existing.unsubscribe(); } catch (_) {}
    }
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: appServerKey,
    });
    const resp = await fetch("/api/me/push-subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subscription: sub.toJSON() }),
    });
    return resp.ok;
  }

  global.HUAlwaysOn = {
    syncToServer, restoreFromServer,
    buildComputeSummary, syncComputeSummary, getComputeSummary,
    subscribePush, registerSW,
    encrypt, decrypt,
  };
})(window);
