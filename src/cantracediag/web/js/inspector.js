"use strict";
/* CanTraceDiag UI — inspector domain. Frame inspector panel. */

/* ---- inspector (AC6) ---------------------------------------------------- */
function clearInspector() {
  $("inspBody").innerHTML = `<div class="insp-empty">Select a trace row to inspect it.</div>`;
}

async function showInspector(row) {
  let html = "";
  if (row.kind === "frame") {
    // Instrument header: arbitration id in large mono, message + DBC subtitle,
    // raw payload highlighted in an "instrument screen" block.
    const msgParts = [row.name ?? "(undecoded)"];
    if (row.dbc_source) msgParts.push(row.dbc_source);
    html += `<div class="insp-id">${esc(row.id_hex ?? "—")}</div>` +
      `<div class="insp-msg">${esc(msgParts.join(" · "))}</div>`;
    if (row.data_hex) html += `<div class="insp-raw">${esc(String(row.data_hex).toUpperCase())}</div>`;
    const rows = [
      ["Timestamp", fmtTime(row.timestamp_s)],
      ["Channel", row.channel ?? "—"],
      ["Direction", row.direction ?? "—"],
      ["DLC", row.dlc ?? "—"],
      ["Decode status", row.decode_status ?? "—"],
    ];
    html += `<dl class="insp-grid">` +
      rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("") + `</dl>`;
    if (row.id_hex) html += `<div class="insp-sec">Decoded signals</div><div id="inspSignals" class="insp-empty">loading…</div>`;
  } else {
    const rows = [
      ["Timestamp", fmtTime(row.timestamp_s)],
      ["Kind", row.kind],
      ["Channel", row.channel ?? "—"],
      ["Event", row.name ?? "—"],
      ["Detail", row.detail ?? "—"],
    ];
    html += `<dl class="insp-grid">` +
      rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("") + `</dl>`;
  }
  $("inspBody").innerHTML = html;

  if (row.kind === "frame" && row.id_hex) {
    try {
      const id = parseInt(row.id_hex, 16);
      const r = await api(`/api/frame-signals?at=${row.timestamp_s}&id=${id}`);
      const box = $("inspSignals");
      if (!r.signals.length) { box.textContent = "no decoded signals"; box.className = "insp-empty"; return; }
      box.className = "";
      box.innerHTML = r.signals.map((s) => {
        const v = s.value_num ?? s.value_text;
        return `<div class="insp-sig"><span>${esc(s.signal_name)}</span><span class="v">${esc(`${v}${s.unit ? " " + s.unit : ""}`)}</span></div>`;
      }).join("");
    } catch (err) {
      console.warn("Inspector signal lookup failed", err);
      const box = $("inspSignals");
      if (box) box.textContent = "decoded signals unavailable";
    }
  }
}

