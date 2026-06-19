let stagesData = [];

function show(id) { document.getElementById(id).classList.remove("hidden"); }
function hide(id) { document.getElementById(id).classList.add("hidden"); }
function text(id, val) { document.getElementById(id).textContent = val; }

async function fetchJSON(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

async function loadAll() {
  hide("stages-table-wrap");
  hide("stages-empty");
  hide("stages-error");
  show("stages-loading");
  hide("detail-section");
  text("kpi-records", "—");
  text("kpi-errors", "—");
  text("kpi-rate", "—");
  text("kpi-pc-rate", "—");

  try {
    const [summary, pcSummary, stages] = await Promise.all([
      fetchJSON("/api/summary"),
      fetchJSON("/api/prompt-chain").catch(() => ({ success_rate: 0 })),
      fetchJSON("/api/stages"),
    ]);

    text("kpi-records", summary.total_records ?? 0);
    text("kpi-errors", summary.total_errors ?? 0);
    text("kpi-rate", (summary.success_rate ?? 0) + "%");

    const pcRate = pcSummary.success_rate;
    text("kpi-pc-rate", pcRate != null ? pcRate + "%" : "N/A");

    stagesData = stages;
    renderStages(stages);
    hide("stages-loading");
    hide("stages-error");
    if (stages.length === 0) {
      show("stages-empty");
    } else {
      show("stages-table-wrap");
    }
  } catch (err) {
    hide("stages-loading");
    show("stages-error");
    text("stages-error", "Error loading data: " + err.message);
  }
}

function renderStages(stages) {
  const tbody = document.getElementById("stages-body");
  tbody.innerHTML = stages.map((s) =>
    `<tr onclick="selectStage('${s.name}')" data-stage="${s.name}">
      <td>${s.name}</td>
      <td>${s.runs}</td>
      <td>${s.errors}</td>
      <td>${s.success_rate}%</td>
    </tr>`
  ).join("");
}

function selectStage(name) {
  document.querySelectorAll("#stages-body tr").forEach((tr) => {
    tr.classList.toggle("selected", tr.dataset.stage === name);
  });
  loadDetail(name);
}

async function loadDetail(stage) {
  hide("detail-content");
  hide("detail-empty");
  hide("detail-error");
  show("detail-loading");
  show("detail-section");
  text("detail-title", stage);

  try {
    const records = await fetchJSON(`/api/stages/${stage}/recent?limit=20`);
    hide("detail-loading");
    if (records.length === 0) {
      show("detail-empty");
    } else {
      const content = document.getElementById("detail-content");
      content.innerHTML = "<pre>" + escapeHTML(JSON.stringify(records, null, 2)) + "</pre>";
      show("detail-content");
    }
  } catch (err) {
    hide("detail-loading");
    show("detail-error");
    text("detail-error", "Error: " + err.message);
  }
}

function escapeHTML(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

let sortAsc = {};
function sortStages(field) {
  const asc = !(sortAsc[field] ?? true);
  sortAsc[field] = asc;
  stagesData.sort((a, b) => {
    const va = a[field], vb = b[field];
    if (typeof va === "string") return asc ? va.localeCompare(vb) : vb.localeCompare(va);
    return asc ? va - vb : vb - va;
  });
  renderStages(stagesData);

  document.querySelectorAll("#stages-table th").forEach((th) => {
    th.classList.remove("sorted-asc", "sorted-desc");
    if (th.dataset.sort === field) {
      th.classList.add(asc ? "sorted-asc" : "sorted-desc");
    }
  });
}

document.addEventListener("DOMContentLoaded", loadAll);
