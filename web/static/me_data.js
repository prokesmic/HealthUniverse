/**
 * Health Universe — /me/data hub controller.
 *
 * Hydrates UI from HUPersonal (localStorage), wires up all five
 * sections (labs, wearables, genetics, records, protocols), handles
 * uploads, and calls the stateless evidence-overlay API endpoints.
 */
(function () {
  "use strict";
  const HU = window.HUPersonal;
  if (!HU) return;

  // ─── Tabs ───────────────────────────────────────────────────────
  document.querySelectorAll(".data-tabs button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;
      document.querySelectorAll(".data-tabs button").forEach((b) => b.classList.toggle("is-active", b === btn));
      document.querySelectorAll(".data-pane").forEach((p) => {
        const active = p.dataset.pane === target;
        p.classList.toggle("is-active", active);
        p.style.display = active ? "block" : "none";
      });
    });
  });

  // ─── Hub headline counter + summary ────────────────────────────
  function renderHub() {
    const c = HU.counts();
    const total = c.labs + c.wearable_points + c.genetics + c.records + c.protocols;
    const txt = total === 0
      ? "No data added yet — start anywhere"
      : `${total} data point${total === 1 ? "" : "s"} across ${[
          c.labs ? "labs" : null,
          c.wearable_points ? "wearables" : null,
          c.genetics ? "genetics" : null,
          c.records ? "records" : null,
          c.protocols ? "protocols" : null,
        ].filter(Boolean).join(" · ")}`;
    document.getElementById("hub-counter-text").textContent = txt;

    const sum = document.getElementById("hub-summary");
    sum.innerHTML = "";
    [
      { n: c.labs,             lbl: "lab values" },
      { n: c.wearable_points,  lbl: "wearable points" },
      { n: c.genetics,         lbl: "genetic variants" },
      { n: c.records,          lbl: "medical records" },
      { n: c.protocols,        lbl: "n-of-1 protocols" },
    ].forEach((s) => {
      const div = document.createElement("div");
      div.className = "hub-stat" + (s.n === 0 ? " is-empty" : "");
      div.innerHTML = `<div class="n">${s.n}</div><div class="lbl">${s.lbl}</div>`;
      sum.appendChild(div);
    });

    document.getElementById("labs-count").textContent      = `${c.labs} added`;
    document.getElementById("wearables-count").textContent = `${c.wearable_points} points`;
    document.getElementById("genetics-count").textContent  = `${c.genetics} variant${c.genetics === 1 ? "" : "s"}`;
    document.getElementById("records-count").textContent   = `${c.records} record${c.records === 1 ? "" : "s"}`;
    document.getElementById("protocols-count").textContent = `${c.protocols} active`;
  }

  // ─── Empty-state pitch helper ──────────────────────────────────
  function emptyPitch(host, title, body, example) {
    host.innerHTML = `
      <div class="empty-pitch">
        <div class="pitch-title">${title}</div>
        <div>${body}</div>
        ${example ? `<div class="pitch-example">${example}</div>` : ""}
      </div>`;
  }

  // ─── LABS ──────────────────────────────────────────────────────
  async function renderLabs() {
    const s = HU.load();
    const list = document.getElementById("lab-list");
    const empty = document.getElementById("labs-empty");
    list.innerHTML = "";
    if (s.labs.length === 0) {
      emptyPitch(empty,
        "Add your first lab to see what it means.",
        "Sample: <code>TSH 3.8 mIU/L</code> — over the 4.0 reference, " +
        "lights up the subclinical-hypothyroid edge cluster, " +
        "surfaces 5 protective interventions backed by tier-A/B evidence. " +
        "You'll see exactly the same level of detail for any of your labs.",
        "TSH · 3.8 · mIU/L · 2026-05-09 — out of range (high) · 5 evidence edges activated");
      return;
    }
    empty.innerHTML = "";

    // Sort newest-first.
    const sorted = [...s.labs].sort((a, b) => b.date.localeCompare(a.date) || b.added_at.localeCompare(a.added_at));
    for (const lab of sorted) {
      const li = document.createElement("li");
      li.className = "data-item";
      li.dataset.id = lab.id;
      li.innerHTML = `
        <div class="item-head">
          <span class="item-name">${escapeHTML(lab.name)}</span>
          <span class="item-value">${lab.value}</span>
          <span class="item-meta">${escapeHTML(lab.unit || "")}</span>
          <span class="item-meta">· ${lab.date}</span>
          <div class="item-actions">
            <button class="item-delete" data-del-lab="${lab.id}">delete</button>
          </div>
        </div>
        <div class="item-evidence" data-lab-evidence>Looking up evidence…</div>
      `;
      list.appendChild(li);
      // Async fetch evidence overlay.
      const ev = li.querySelector("[data-lab-evidence]");
      try {
        const r = await fetch(
          `/api/me/lab-evidence?name=${encodeURIComponent(lab.name)}&value=${encodeURIComponent(lab.value)}&unit=${encodeURIComponent(lab.unit || "")}`
        );
        const j = await r.json();
        if (!j.matched) {
          ev.innerHTML = `<span class="pill-mini pm-mute">⚙ no panel match</span> ${escapeHTML(j.message || "Not in our reference panel yet.")}`;
          continue;
        }
        const dirPill = j.out_of_range
          ? `<span class="pill-mini pm-bad">${j.direction}</span>`
          : `<span class="pill-mini pm-good">in range (${j.ref_low}–${j.ref_high} ${j.unit || ""})</span>`;
        const explainer = j.explainer ? `<div style="margin-top:4px">${escapeHTML(j.explainer)}</div>` : "";
        let lines = [`${dirPill}`];
        if (j.out_of_range) {
          if (j.edges && j.edges.length) {
            lines.push(`<div style="margin-top:6px"><b>${j.edges.length}</b> edge${j.edges.length === 1 ? "" : "s"} where this lab is the factor:</div>`);
            const top = j.edges.slice(0, 3);
            lines.push(`<ul style="margin:4px 0 4px 20px;padding:0;font-size:12px">${top.map((e) =>
              `<li><a href="/edge/${e.id}">${escapeHTML(e.f_name)} → ${escapeHTML(e.o_name)}</a> · <span class="pill-mini pm-info">${e.tier}</span></li>`
            ).join("")}</ul>`);
            if (j.edges.length > 3) lines.push(`<small class="muted">+ ${j.edges.length - 3} more — see your <a href="/my-plan">plan</a></small>`);
          }
          if (j.interventions && j.interventions.length) {
            lines.push(`<div style="margin-top:6px"><b>What helps</b> (top protective edges):</div>`);
            lines.push(`<ul style="margin:4px 0 4px 20px;padding:0;font-size:12px">${j.interventions.slice(0, 4).map((e) =>
              `<li><a href="/edge/${e.id}">${escapeHTML(e.f_name)}</a> for ${escapeHTML(e.o_name)} · <span class="pill-mini pm-info">${e.tier}</span></li>`
            ).join("")}</ul>`);
          }
          li.classList.add("is-out");
        } else {
          li.classList.add("is-good");
        }
        ev.innerHTML = lines.join("") + explainer;
      } catch (e) {
        ev.innerHTML = `<span class="muted small">evidence lookup failed</span>`;
      }
    }
    // Wire deletes.
    list.querySelectorAll("[data-del-lab]").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (confirm("Remove this lab?")) HU.deleteLab(btn.dataset.delLab);
      });
    });
  }

  document.getElementById("lab-add-form").addEventListener("submit", (ev) => {
    ev.preventDefault();
    HU.addLab({
      name:  document.getElementById("lab-name").value,
      value: document.getElementById("lab-value").value,
      unit:  document.getElementById("lab-unit").value,
      date:  document.getElementById("lab-date").value || undefined,
      source: "manual",
    });
    ev.target.reset();
  });

  // Lab image / PDF upload → AI parse → user review → save.
  document.getElementById("lab-image-upload").addEventListener("change", async (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    const results = document.getElementById("lab-parse-results");
    const tbody = document.getElementById("lab-parse-tbody");
    const summary = document.getElementById("lab-parse-summary");
    const saveBtn = document.getElementById("lab-parse-save");
    saveBtn.disabled = true;
    results.style.display = "block";
    tbody.innerHTML = "";
    summary.textContent = `Parsing ${f.name}… (typically 10-25 seconds)`;
    const fd = new FormData();
    fd.append("file", f);
    try {
      const r = await fetch("/api/me/parse-lab-image", { method: "POST", body: fd });
      if (r.status === 401) {
        summary.innerHTML = `<span style="color:#9b1c1c">Sign in first to parse images.</span> <button class="btn-secondary inline" onclick="document.getElementById('account-signin-btn')?.click()">Sign in →</button>`;
        return;
      }
      if (r.status === 402) {
        const j = await r.json().catch(() => ({}));
        summary.innerHTML = `<div style="padding:10px 12px;background:linear-gradient(180deg,#fffbe7,#fff5d6);border:1px solid #f0d68a;border-radius:8px"><b style="color:#7a5c00">Pro feature</b><div style="margin-top:4px;font-size:13px">${escapeHTML(j.message || "AI lab parsing is part of the Pro tier.")}</div><a href="${j.upgrade_url || "/stack"}" class="btn-primary inline" style="margin-top:8px;display:inline-block;text-decoration:none">Join the Pro waitlist →</a></div>`;
        return;
      }
      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        summary.innerHTML = `<span style="color:#9b1c1c">Parse failed (${r.status}): ${escapeHTML(j.message || j.error || "unknown error")}</span>`;
        return;
      }
      const j = await r.json();
      const labs = j.labs || [];
      if (labs.length === 0) {
        summary.innerHTML = `<span style="color:#9b1c1c">No lab values found in this file.</span>`;
        return;
      }
      summary.innerHTML = `Found <b>${labs.length}</b> value${labs.length === 1 ? "" : "s"} via <code>${escapeHTML(j.backend)}</code>. Uncheck anything wrong, edit fields inline, then save.`;
      labs.forEach((lab, i) => {
        const tr = document.createElement("tr");
        tr.style.borderBottom = "1px solid var(--line)";
        tr.innerHTML = `
          <td style="padding:4px"><input type="checkbox" data-i="${i}" checked></td>
          <td style="padding:4px"><input data-i="${i}" data-k="name" value="${escapeHTML(lab.name || "")}" style="width:100%; padding:4px; border:1px solid var(--line); border-radius:4px"></td>
          <td style="padding:4px"><input data-i="${i}" data-k="value" type="number" step="0.01" value="${lab.value != null ? lab.value : ""}" style="width:80px; padding:4px; border:1px solid var(--line); border-radius:4px"></td>
          <td style="padding:4px"><input data-i="${i}" data-k="unit" value="${escapeHTML(lab.unit || "")}" style="width:80px; padding:4px; border:1px solid var(--line); border-radius:4px"></td>
          <td style="padding:4px"><input data-i="${i}" data-k="date" type="date" value="${escapeHTML(lab.date || "")}" style="padding:4px; border:1px solid var(--line); border-radius:4px"></td>
        `;
        tbody.appendChild(tr);
      });
      saveBtn.disabled = false;
    } catch (e) {
      summary.innerHTML = `<span style="color:#9b1c1c">Network error: ${escapeHTML(String(e))}</span>`;
    }
    ev.target.value = "";
  });

  // Select-all / save / cancel handlers for the parse-results table.
  document.getElementById("lab-parse-all").addEventListener("change", (ev) => {
    document.querySelectorAll("#lab-parse-tbody input[type=checkbox]")
      .forEach((cb) => { cb.checked = ev.target.checked; });
  });
  document.getElementById("lab-parse-cancel").addEventListener("click", () => {
    document.getElementById("lab-parse-results").style.display = "none";
    document.getElementById("lab-parse-tbody").innerHTML = "";
  });
  document.getElementById("lab-parse-save").addEventListener("click", () => {
    const rows = document.querySelectorAll("#lab-parse-tbody tr");
    let saved = 0;
    rows.forEach((tr) => {
      const cb = tr.querySelector('input[type="checkbox"]');
      if (!cb || !cb.checked) return;
      const name = tr.querySelector('input[data-k=name]').value.trim();
      const value = tr.querySelector('input[data-k=value]').value;
      const unit = tr.querySelector('input[data-k=unit]').value.trim();
      const date = tr.querySelector('input[data-k=date]').value || undefined;
      if (name && value && !isNaN(Number(value))) {
        HU.addLab({ name, value, unit, date, source: "ai-parsed" });
        saved++;
      }
    });
    document.getElementById("lab-parse-results").style.display = "none";
    document.getElementById("lab-parse-tbody").innerHTML = "";
    if (saved) document.querySelector('[data-tab=labs]').click();
  });

  document.getElementById("lab-csv-upload").addEventListener("change", (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => {
      const lines = r.result.split(/\r?\n/).filter((x) => x.trim());
      const head = lines[0].toLowerCase().split(",").map((x) => x.trim());
      const ix = (k) => head.indexOf(k);
      const hasHeader = ix("name") >= 0 && ix("value") >= 0;
      const start = hasHeader ? 1 : 0;
      let added = 0;
      for (let i = start; i < lines.length; i++) {
        const cols = lines[i].split(",").map((x) => x.trim().replace(/^"|"$/g, ""));
        const name = hasHeader ? cols[ix("name")] : cols[0];
        const value = hasHeader ? cols[ix("value")] : cols[1];
        const unit = hasHeader && ix("unit") >= 0 ? cols[ix("unit")] : (cols[2] || "");
        const date = hasHeader && ix("date") >= 0 ? cols[ix("date")] : (cols[3] || undefined);
        if (name && value && !isNaN(Number(value))) {
          HU.addLab({ name, value, unit, date, source: "csv" });
          added++;
        }
      }
      alert(`Imported ${added} lab values.`);
      ev.target.value = "";
    };
    r.readAsText(f);
  });

  // ─── WEARABLES ─────────────────────────────────────────────────
  function renderWearables() {
    const s = HU.load();
    const empty = document.getElementById("wearables-empty");
    const wrap = document.getElementById("wearable-trends");
    wrap.innerHTML = "";
    const total = Object.values(s.wearables).reduce((a, b) => a + b.length, 0);
    if (total === 0) {
      emptyPitch(empty,
        "Track one number a week and you'll see drift before your GP does.",
        "Resting heart rate creeping up over 6 weeks usually means accumulating sleep debt, " +
        "rising training load, or under-recovery. We'll spot it and tell you which factors in " +
        "the corpus most likely explain it.",
        "RHR · 58 → 63 bpm over 6 weeks · 3 likely drivers in your stack");
      return;
    }
    empty.innerHTML = "";

    const labels = {
      rhr: { name: "Resting HR", unit: "bpm", betterDirection: "down" },
      sleep_hours: { name: "Sleep", unit: "h", betterDirection: "up" },
      weight: { name: "Weight", unit: "" },
      hrv: { name: "HRV", unit: "ms", betterDirection: "up" },
      steps: { name: "Steps", unit: "/day", betterDirection: "up" },
      glucose: { name: "Glucose", unit: "mg/dL", betterDirection: "down" },
    };
    Object.keys(s.wearables).forEach((stream) => {
      const pts = s.wearables[stream];
      if (!pts.length) return;
      const last7 = pts.slice(-21);
      const card = document.createElement("div");
      card.className = "trend-card";
      const latest = pts[pts.length - 1];
      const earliest = last7[0];
      const delta = latest.value - earliest.value;
      const lbl = labels[stream] || { name: stream, unit: "" };
      const deltaClass = lbl.betterDirection === "up"
        ? (delta >= 0 ? "down" : "up")
        : (delta <= 0 ? "down" : "up");
      const arrow = delta > 0 ? "↑" : (delta < 0 ? "↓" : "→");
      const range = pts.reduce((acc, p) => ({ min: Math.min(acc.min, p.value), max: Math.max(acc.max, p.value) }),
        { min: pts[0].value, max: pts[0].value });
      const W = 220, H = 50, PAD = 4;
      const span = (range.max - range.min) || 1;
      const points = last7.map((p, i) => {
        const x = PAD + ((W - 2 * PAD) * i) / Math.max(last7.length - 1, 1);
        const y = H - PAD - ((H - 2 * PAD) * (p.value - range.min)) / span;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(" ");
      const areaPath = points
        ? `M ${points.split(" ")[0]} L ${points} L ${W - PAD},${H - PAD} L ${PAD},${H - PAD} Z`
        : "";
      card.innerHTML = `
        <h4>${lbl.name}</h4>
        <span class="latest">${latest.value}<small style="font-size:13px;color:#888;margin-left:3px">${lbl.unit}</small></span>
        <span class="delta ${deltaClass}">${arrow} ${Math.abs(delta).toFixed(1)} over ${last7.length} pts</span>
        <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
          <path class="trend-area" d="${areaPath}" />
          <polyline class="trend-line" points="${points}" />
        </svg>
        <div class="muted small" style="margin-top:4px">${pts.length} total · range ${range.min}–${range.max}</div>
      `;
      wrap.appendChild(card);
    });
  }

  document.getElementById("wearable-add-btn").addEventListener("click", () => {
    const stream = document.getElementById("wearable-stream").value;
    const value = document.getElementById("wearable-value").value;
    const date = document.getElementById("wearable-date").value || undefined;
    if (!value) return;
    HU.addWearablePoint(stream, { value, date });
    document.getElementById("wearable-value").value = "";
  });

  document.getElementById("wearable-csv-upload").addEventListener("change", (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => {
      const lines = r.result.split(/\r?\n/).filter((x) => x.trim());
      const head = lines[0].toLowerCase().split(",").map((x) => x.trim());
      const ix = (k) => head.indexOf(k);
      const hasHeader = ix("date") >= 0 && ix("value") >= 0;
      const start = hasHeader ? 1 : 0;
      const defaultStream = document.getElementById("wearable-stream").value;
      const buckets = {};
      for (let i = start; i < lines.length; i++) {
        const cols = lines[i].split(",").map((x) => x.trim().replace(/^"|"$/g, ""));
        const stream = hasHeader && ix("stream") >= 0 ? cols[ix("stream")] : defaultStream;
        const date = hasHeader ? cols[ix("date")] : cols[0];
        const value = hasHeader ? cols[ix("value")] : cols[1];
        if (date && value && !isNaN(Number(value))) {
          buckets[stream] = buckets[stream] || [];
          buckets[stream].push({ date, value });
        }
      }
      let added = 0;
      Object.entries(buckets).forEach(([stream, points]) => {
        HU.bulkAddWearable(stream, points);
        added += points.length;
      });
      alert(`Imported ${added} points.`);
      ev.target.value = "";
    };
    r.readAsText(f);
  });

  // ─── GENETICS ──────────────────────────────────────────────────
  async function renderGenetics() {
    const s = HU.load();
    const list = document.getElementById("snp-list");
    const empty = document.getElementById("genetics-empty");
    list.innerHTML = "";
    if (s.genetics.length === 0) {
      emptyPitch(empty,
        "Add a few rsIDs (or drop your 23andMe raw file) to see how your variants modulate the plan.",
        "We focus on the 20+ most actionable SNPs only — APOE, MTHFR, FTO, " +
        "CYP2D6, COMT, CYP1A2 (caffeine), TCF7L2 (T2D), ACTN3 (athletic) — and ignore the rest. " +
        "Each variant tells us which edges in your plan should weight more heavily.",
        "rs429358 · CT (APOE ε3/ε4) → dementia-prevention edges weight 1.5×");
      return;
    }
    empty.innerHTML = "";
    for (const v of s.genetics) {
      const li = document.createElement("li");
      li.className = "data-item";
      li.innerHTML = `
        <div class="item-head">
          <span class="item-name">${v.rsid}</span>
          <span class="item-value">${v.genotype}</span>
          <span class="item-meta">· ${v.source || "manual"}</span>
          <div class="item-actions">
            <button class="item-delete" data-del-snp="${v.id}">delete</button>
          </div>
        </div>
        <div class="item-evidence" data-snp-evidence>Looking up…</div>
      `;
      list.appendChild(li);
      const ev = li.querySelector("[data-snp-evidence]");
      try {
        const r = await fetch(`/api/me/snp-evidence?rsid=${encodeURIComponent(v.rsid)}&genotype=${encodeURIComponent(v.genotype)}`);
        const j = await r.json();
        if (!j.matched) {
          ev.innerHTML = `<span class="pill-mini pm-mute">⚙ not in panel</span> ${escapeHTML(j.message || "")}`;
          continue;
        }
        const lines = [
          `<div><b>${escapeHTML(j.name)}</b> · <span class="pill-mini pm-info">${escapeHTML(j.gene || "")}</span></div>`,
        ];
        if (j.label) lines.push(`<div style="margin-top:3px;font-weight:600">${escapeHTML(j.label)}</div>`);
        if (j.summary) lines.push(`<div style="margin-top:3px">${escapeHTML(j.summary)}</div>`);
        if (j.amplify_factor) {
          lines.push(`<div style="margin-top:6px"><span class="pill-mini pm-warn">×${j.amplify_factor}</span> ${j.edges.length} relevant edge${j.edges.length === 1 ? "" : "s"} amplified in your plan.</div>`);
        }
        ev.innerHTML = lines.join("");
      } catch (e) {
        ev.innerHTML = `<span class="muted small">lookup failed</span>`;
      }
    }
    list.querySelectorAll("[data-del-snp]").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (confirm("Remove this variant?")) HU.deleteVariant(btn.dataset.delSnp);
      });
    });
  }

  document.getElementById("snp-add-form").addEventListener("submit", (ev) => {
    ev.preventDefault();
    HU.addVariant({
      rsid:    document.getElementById("snp-rsid").value,
      genotype: document.getElementById("snp-genotype").value,
    });
    ev.target.reset();
  });

  document.getElementById("snp-file-upload").addEventListener("change", (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => {
      // 23andMe raw text format: rsid\tchromosome\tposition\tgenotype
      // (header lines start with #). Ancestry uses tabs too, slightly
      // different columns; both have rsid as col 0 and a 2-letter
      // genotype as the last column.
      const rows = [];
      const lines = r.result.split(/\r?\n/);
      for (const line of lines) {
        if (!line || line.startsWith("#")) continue;
        const cols = line.split(/\t|,/).map((x) => x.trim());
        const rsid = (cols[0] || "").toLowerCase();
        const last = (cols[cols.length - 1] || "").toUpperCase();
        if (!rsid.startsWith("rs")) continue;
        // Genotype is two letters; sometimes "AA" or "A A".
        const geno = last.replace(/\s+/g, "");
        if (geno.length === 2 && /^[ACGT]+$/.test(geno)) {
          rows.push({ rsid, genotype: geno, source: "23andMe" });
        }
      }
      // Filter to our actionable panel only — pull SNP list.
      fetch("/static/snp_panel_keys.json").then((res) => res.ok ? res.json() : null).then((keys) => {
        const filtered = keys ? rows.filter((r) => keys.includes(r.rsid)) : rows;
        HU.bulkAddVariants(filtered);
        alert(`Imported ${filtered.length} actionable variants (of ${rows.length} total parsed).`);
      }).catch(() => {
        HU.bulkAddVariants(rows);
        alert(`Imported ${rows.length} variants.`);
      });
      ev.target.value = "";
    };
    r.readAsText(f);
  });

  // ─── RECORDS ───────────────────────────────────────────────────
  // Lightweight client-side noun-phrase extraction. We look for known
  // entity slugs and human-readable terms ("disc degeneration",
  // "atherosclerosis", "fatty liver") in the pasted text.
  const RECORD_KEYWORDS = [
    ["atherosclerosis", "atherosclerosis"], ["coronary artery", "cvd"], ["plaque", "atherosclerosis"],
    ["fatty liver", "nafld"], ["nafld", "nafld"],
    ["disc degeneration", "disc_degeneration"], ["disc bulge", "disc_degeneration"],
    ["osteopenia", "osteopenia"], ["osteoporosis", "osteoporosis"],
    ["hashimoto", "autoimmune_thyroiditis"],
    ["hypertension", "hypertension"],
    ["hba1c", "hba1c_high"], ["prediabetes", "prediabetes"],
    ["ldl", "ldl_c"], ["lipoprotein(a)", "lpa_high"], ["apob", "apob"],
    ["ferritin", "high_ferritin"],
    ["fibroid", "uterine_fibroid"],
    ["mci", "cognitive_decline"],
  ];
  function extractFindings(text) {
    const t = (text || "").toLowerCase();
    const seen = new Set();
    for (const [needle, slug] of RECORD_KEYWORDS) {
      if (t.includes(needle)) seen.add(slug);
    }
    return [...seen];
  }
  async function renderRecords() {
    const s = HU.load();
    const list = document.getElementById("record-list");
    const empty = document.getElementById("records-empty");
    list.innerHTML = "";
    if (s.records.length === 0) {
      emptyPitch(empty,
        "Paste a radiology / pathology / specialist report to extract findings.",
        "We extract noun phrases that match entities in our graph and surface " +
        "evidence + interventions for each — so you walk into the next " +
        "appointment with a list of evidence-backed questions.",
        "MRI L-spine: 'mild disc desiccation L4-L5' → 5 evidence-based " +
        "interventions, 2 things to avoid, 3 questions for your orthopedist");
      return;
    }
    empty.innerHTML = "";
    for (const rec of [...s.records].sort((a, b) => b.date.localeCompare(a.date))) {
      const li = document.createElement("li");
      li.className = "data-item";
      const findChips = rec.findings.map((f) => `<span class="pill-mini pm-info" data-finding="${f}">${f.replace(/_/g, " ")}</span>`).join(" ");
      li.innerHTML = `
        <div class="item-head">
          <span class="item-name">${escapeHTML(rec.label || rec.type)}</span>
          <span class="item-meta">${escapeHTML(rec.type)} · ${rec.date}</span>
          <div class="item-actions">
            <button class="item-delete" data-del-record="${rec.id}">delete</button>
          </div>
        </div>
        <div style="font-size:13px;color:var(--ink-soft);max-height:80px;overflow:hidden">${escapeHTML(rec.text || "").slice(0, 400)}${rec.text && rec.text.length > 400 ? "…" : ""}</div>
        <div class="item-evidence">
          <div><b>Findings extracted:</b> ${rec.findings.length === 0 ? "<i>none in our panel</i>" : findChips}</div>
          <div data-record-evidence style="margin-top:6px"></div>
        </div>
      `;
      list.appendChild(li);
      const target = li.querySelector("[data-record-evidence]");
      const lines = [];
      for (const f of rec.findings) {
        try {
          const r = await fetch(`/api/me/finding-evidence?slug=${encodeURIComponent(f)}`);
          const j = await r.json();
          if (j.matched && (j.edges.length || j.interventions.length)) {
            lines.push(`<div style="margin-top:6px"><b>${f.replace(/_/g, " ")}:</b> ${j.edges.length} edges · ${j.interventions.length} interventions — see <a href="/edge/${(j.edges[0] || j.interventions[0] || {}).id || ""}">corpus</a></div>`);
          }
        } catch (e) { /* swallow */ }
      }
      if (lines.length) target.innerHTML = lines.join("");
    }
    list.querySelectorAll("[data-del-record]").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (confirm("Delete this record?")) HU.deleteRecord(btn.dataset.delRecord);
      });
    });
  }

  document.getElementById("record-add-form").addEventListener("submit", (ev) => {
    ev.preventDefault();
    const text = document.getElementById("record-text").value;
    const findings = extractFindings(text);
    HU.addRecord({
      type:  document.getElementById("record-type").value,
      date:  document.getElementById("record-date").value || undefined,
      label: document.getElementById("record-label").value,
      text,
      findings,
    });
    ev.target.reset();
  });

  // ─── PROTOCOLS ─────────────────────────────────────────────────
  function renderProtocols() {
    const s = HU.load();
    const list = document.getElementById("protocol-list");
    const empty = document.getElementById("protocols-empty");
    list.innerHTML = "";
    if (s.protocols.length === 0) {
      emptyPitch(empty,
        "Run an n-of-1 self-experiment to see if YOU respond to a factor.",
        "Pick a factor, log a 1–10 daily score on the outcome you care about, " +
        "and at the end we estimate your personal effect size. The meta-analysis " +
        "tells you the population average; this tells you about you.",
        "Creatine monohydrate · 28 days · daily strength score → personal effect estimate");
      return;
    }
    empty.innerHTML = "";
    const today = new Date().toISOString().slice(0, 10);
    for (const p of [...s.protocols].sort((a, b) => b.started_at.localeCompare(a.started_at))) {
      const days = (new Date(p.ends_at) - new Date(p.started_at)) / 86400000;
      const elapsed = Math.max(0, Math.min(days, (new Date(today) - new Date(p.started_at)) / 86400000));
      const pct = Math.round((elapsed / days) * 100);
      const isComplete = today >= p.ends_at;
      let effect = null;
      if (p.logs.length >= 4) {
        const half = Math.floor(p.logs.length / 2);
        const before = p.logs.slice(0, half).map((l) => l.score);
        const after = p.logs.slice(half).map((l) => l.score);
        const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
        effect = (mean(after) - mean(before)).toFixed(2);
      }
      const li = document.createElement("li");
      li.className = "data-item";
      li.innerHTML = `
        <div class="item-head">
          <span class="item-name">${escapeHTML(p.factor_name || p.factor_slug)} → ${escapeHTML(p.outcome_name || p.outcome_slug)}</span>
          <span class="item-meta">${p.started_at} → ${p.ends_at} · ${pct}% complete · ${p.logs.length} log${p.logs.length === 1 ? "" : "s"}</span>
          <div class="item-actions">
            <button class="item-delete" data-del-protocol="${p.id}">delete</button>
          </div>
        </div>
        ${effect !== null ? `<div class="item-evidence"><b>Personal effect estimate:</b> ${effect > 0 ? "+" : ""}${effect} (later half vs earlier half of your logs). ${isComplete ? "Protocol complete." : "Still in progress — estimate stabilises with more logs."}</div>` : ""}
        <div style="display:flex;gap:6px;align-items:end;flex-wrap:wrap;margin-top:8px">
          <input type="number" min="1" max="10" step="1" placeholder="Score 1-10" id="proto-score-${p.id}" style="width:100px;padding:6px;border:1px solid var(--line);border-radius:4px">
          <input type="text" placeholder="note (optional)" id="proto-note-${p.id}" style="flex:1;padding:6px;border:1px solid var(--line);border-radius:4px;min-width:140px">
          <button class="btn-secondary inline" data-log-protocol="${p.id}">Log today</button>
        </div>
      `;
      list.appendChild(li);
    }
    list.querySelectorAll("[data-del-protocol]").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (confirm("Delete this protocol?")) HU.deleteProtocol(btn.dataset.delProtocol);
      });
    });
    list.querySelectorAll("[data-log-protocol]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.logProtocol;
        const score = document.getElementById("proto-score-" + id).value;
        const note = document.getElementById("proto-note-" + id).value;
        if (!score) return;
        HU.logProtocol(id, { score, note });
      });
    });
  }

  document.getElementById("protocol-add-form").addEventListener("submit", (ev) => {
    ev.preventDefault();
    const factor = document.getElementById("protocol-factor").value.trim();
    const outcome = document.getElementById("protocol-outcome").value.trim();
    HU.addProtocol({
      factor_slug:  factor,
      factor_name:  factor.replace(/_/g, " "),
      outcome_slug: outcome,
      outcome_name: outcome.replace(/_/g, " "),
      duration_days: Number(document.getElementById("protocol-duration").value),
    });
    ev.target.reset();
  });

  // ─── Tools ─────────────────────────────────────────────────────
  document.getElementById("export-btn").addEventListener("click", () => {
    const blob = new Blob([HU.exportJSON()], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "health-universe-personal-data.json";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  document.getElementById("import-file").addEventListener("change", (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => {
      const ok = HU.importJSON(r.result);
      alert(ok ? "Imported." : "Import failed — file wasn't valid JSON.");
      ev.target.value = "";
    };
    r.readAsText(f);
  });
  document.getElementById("clear-btn").addEventListener("click", () => {
    if (confirm("Delete ALL personal data from this browser? This cannot be undone (export first).")) HU.clearAll();
  });

  // ─── Render-all + reactive refresh on store changes ─────────────
  function renderAll() {
    renderHub();
    renderLabs();
    renderWearables();
    renderGenetics();
    renderRecords();
    renderProtocols();
  }
  document.addEventListener("hu-personal-changed", renderAll);
  renderAll();

  // ─── Tiny escape helper ────────────────────────────────────────
  function escapeHTML(s) {
    return String(s || "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
})();
