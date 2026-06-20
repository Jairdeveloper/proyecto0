/* PDCA-sdlc Dashboard — Frontend logic (vanilla JS, 0 dependencies) */

/* ---- State ---- */
let projectsCache = [];
let sortField = null;
let sortAsc = true;
let eventSource = null;
let currentProjectId = null;

/* ---- Init ---- */
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
});

/* ---- Loading overlay ---- */
function showLoading(show) {
  document.getElementById('loading').style.display = show ? 'flex' : 'none';
}

/* ---- Dashboard overview ---- */
async function loadDashboard() {
  showLoading(true);
  try {
    const endpoints = [
      fetch('/api/projects'),
      fetch('/api/agents'),
      fetch('/api/events?project=_all&limit=1'),
      fetch('/api/events/distribution?project=_all'),
      fetch('/api/health/metrics'),
    ];
    const [projRes, agentsRes, eventsRes, distRes, metricsRes] = await Promise.all(endpoints);
    const projects = await projRes.json();
    const agents = await agentsRes.json();
    const dist = await distRes.json();
    const metrics = await metricsRes.json();

    let totalEvents = 0;
    let totalArtifacts = 0;
    if (projects.projects && projects.projects.length > 0) {
      for (const p of projects.projects) {
        totalEvents += p.event_count || 0;
        totalArtifacts += p.artifact_count || 0;
      }
    }

    projectsCache = projects.projects || [];

    document.querySelector('#kpi-projects .kpi-value').textContent = projectsCache.length;
    document.querySelector('#kpi-agents .kpi-value').textContent = (agents.total || 0) + ' active';
    document.querySelector('#kpi-events .kpi-value').textContent = totalEvents;
    document.querySelector('#kpi-artifacts .kpi-value').textContent = totalArtifacts;
    document.querySelector('#kpi-usage .kpi-value').textContent = (metrics.usage_pct || 0) + '%';

    renderDistributionChart('distribution-chart', dist.distribution || {});
    renderTopicList(dist.distribution || {});
    renderTimelineSVG('timeline-svg', []);
    renderProjects(projectsCache);
  } catch (err) {
    document.getElementById('projects-body').innerHTML =
      '<tr><td colspan="5" class="error-msg">Error al cargar: ' + escapeHTML(err.message) + '</td></tr>';
  } finally {
    showLoading(false);
  }
}

/* ---- Distribution Bar Chart (Canvas API) ---- */
function renderDistributionChart(canvasId, distribution) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const entries = Object.entries(distribution);
  if (entries.length === 0) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }
  const maxVal = Math.max(...Object.values(distribution), 1);
  const barArea = canvas.width - 50;
  const barWidth = barArea / (entries.length * 2);
  const chartH = canvas.height - 30;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  entries.forEach(([topic, count], i) => {
    const x = 45 + i * barWidth * 2 + barWidth * 0.3;
    const h = (count / maxVal) * chartH;
    const y = canvas.height - 15 - h;
    const hue = (i * 40) % 360;
    ctx.fillStyle = `hsl(${hue}, 60%, 55%)`;
    ctx.fillRect(x, y, barWidth * 0.7, h);
    ctx.fillStyle = '#aab';
    ctx.font = '9px monospace';
    const label = topic.length > 10 ? topic.substring(0, 8) + '..' : topic;
    ctx.fillText(label, x - 2, canvas.height - 3);
    ctx.fillText(String(count), x + 2, y - 4);
  });
}

/* ---- Topic list sidebar ---- */
function renderTopicList(distribution) {
  const el = document.getElementById('topic-list');
  if (!el) return;
  const entries = Object.entries(distribution);
  if (entries.length === 0) {
    el.innerHTML = '<span class="empty">Sin eventos</span>';
    return;
  }
  el.innerHTML = entries.map(([topic, count]) =>
    `<div class="topic-item"><span class="topic-name">${escapeHTML(topic)}</span><span class="topic-count">${count}</span></div>`
  ).join('');
}

/* ---- Timeline SVG ---- */
function renderTimelineSVG(svgId, buckets) {
  const svg = document.getElementById(svgId);
  if (!svg) return;
  const W = svg.clientWidth || 600;
  const H = 120;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  if (!buckets || buckets.length === 0) {
    svg.innerHTML = `<text x="${W/2}" y="${H/2}" text-anchor="middle" fill="#8899b4" font-size="13">Sin datos de timeline</text>`;
    return;
  }
  const maxC = Math.max(...buckets.map(b => b.count), 1);
  const step = W / Math.max(buckets.length, 1);
  const points = buckets.map((b, i) => {
    const x = i * step + step / 2;
    const y = H - 20 - (b.count / maxC) * (H - 40);
    return `${x},${y}`;
  }).join(' ');
  svg.innerHTML = `<polyline points="${points}" fill="none" stroke="#4a9eff" stroke-width="2"/>`;
}

/* ---- Projects table ---- */
function renderProjects(projects) {
  const tbody = document.getElementById('projects-body');
  if (!projects || projects.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty">No hay proyectos. Ejecuta el pipeline primero.</td></tr>';
    return;
  }
  tbody.innerHTML = projects.map(p => `
    <tr onclick="showProject('${escapeHTML(p.project_id)}')">
      <td><strong>${escapeHTML(p.project_id)}</strong></td>
      <td><span class="tag tag-${p.complexity === 'complex' ? 'failed' : p.complexity === 'moderate' ? 'tag-functional' : 'tag-success'}">${escapeHTML(p.complexity)}</span></td>
      <td>${p.requirement_count}</td>
      <td>${p.artifact_count}</td>
      <td>${p.event_count}</td>
    </tr>
  `).join('');
}

/* ---- Project detail ---- */
async function showProject(projectId) {
  currentProjectId = projectId;
  showLoading(true);
  try {
    const [projRes, traceRes, eventsRes, distRes] = await Promise.all([
      fetch('/api/projects/' + encodeURIComponent(projectId)),
      fetch('/api/projects/' + encodeURIComponent(projectId) + '/trace'),
      fetch('/api/events?project=' + encodeURIComponent(projectId) + '&limit=20'),
      fetch('/api/events/distribution?project=' + encodeURIComponent(projectId)),
    ]);
    const project = await projRes.json();
    const trace = await traceRes.json();
    const events = await eventsRes.json();
    const dist = await distRes.json();

    if (project.error) {
      alert(project.error);
      return;
    }

    document.getElementById('section-projects').style.display = 'none';
    document.getElementById('section-detail').style.display = 'block';
    document.getElementById('detail-title').textContent = projectId;

    renderGoal(project);
    renderRequirements(project);
    renderTrace(trace);
    renderArtifacts(project);
    renderEvents(events);
    renderDistributionChart('detail-distribution-chart', dist.distribution || {});
    fetchAndRenderTimeline(projectId, 'detail-timeline-svg');
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    showLoading(false);
  }
}

async function fetchAndRenderTimeline(projectId, svgId) {
  try {
    const res = await fetch('/api/events/timeline?project=' + encodeURIComponent(projectId) + '&granularity=1m');
    const data = await res.json();
    renderTimelineSVG(svgId, data.buckets || []);
  } catch (e) {
    // silent
  }
}

function showDashboard() {
  currentProjectId = null;
  stopLiveStream();
  document.getElementById('section-detail').style.display = 'none';
  document.getElementById('section-projects').style.display = 'block';
}

/* ---- Goal ---- */
function renderGoal(project) {
  const g = project.goal || {};
  document.getElementById('detail-goal-content').innerHTML = `
    <div class="goal-block">
      <div class="goal-item">
        <div class="label">Descripcion</div>
        <div class="value">${escapeHTML(g.description || '-')}</div>
      </div>
      <div class="goal-item">
        <div class="label">Complejidad</div>
        <div class="value">${escapeHTML(g.complexity || '-')}</div>
      </div>
      <div class="goal-item">
        <div class="label">Lifecycle</div>
        <div class="value">${escapeHTML(g.lifecycle || '-')}</div>
      </div>
      <div class="goal-item">
        <div class="label">Esfuerzo</div>
        <div class="value">${(g.effort_estimate && g.effort_estimate.estimated_hours) ? g.effort_estimate.estimated_hours + 'h / ' + g.effort_estimate.estimated_days + 'd' : '-'}</div>
      </div>
      <div class="goal-item">
        <div class="label">Actividades</div>
        <div class="value">${(g.activities || []).length}</div>
      </div>
    </div>
  `;
}

/* ---- Requirements ---- */
function renderRequirements(project) {
  const reqs = project.requirements || [];
  document.getElementById('reqs-count').textContent = reqs.length;
  const tbody = document.getElementById('reqs-body');
  if (reqs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty">Sin requisitos</td></tr>';
    return;
  }
  tbody.innerHTML = reqs.map(r => `
    <tr>
      <td>${escapeHTML(r.id)}</td>
      <td>${escapeHTML(r.text)}</td>
      <td><span class="tag tag-${r.type === 'non_functional' ? 'non_functional' : 'functional'}">${escapeHTML(r.type)}</span></td>
      <td><span class="tag tag-${r.priority}">${escapeHTML(r.priority)}</span></td>
    </tr>
  `).join('');
}

/* ---- Trace ---- */
function renderTrace(trace) {
  const content = document.getElementById('trace-content');
  if (!trace || !trace.trace || trace.trace.length === 0) {
    content.innerHTML = '<span class="empty">Sin trazabilidad</span>';
    return;
  }
  const nodes = trace.trace;
  let html = '';
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];
    const cls = n.type;
    const label = n.id;
    html += '<div class="trace-node ' + cls + '">';
    if (i > 0) html += '<span class="trace-connector">&#x2514; </span>';
    html += escapeHTML(label);
    if (n.type === 'requirement' && n.properties && n.properties.text) {
      html += ' <span class="trace-connector">—</span> ';
      html += escapeHTML(String(n.properties.text).substring(0, 60));
    }
    if (n.type === 'artifact' && n.properties && n.properties.status) {
      html += ' <span class="tag tag-' + (n.properties.status === 'committed' ? 'success' : 'failed') + '">' + escapeHTML(n.properties.status) + '</span>';
    }
    html += '</div>';
  }
  content.innerHTML = html;
}

/* ---- Artifacts ---- */
function renderArtifacts(project) {
  const artifacts = project.artifacts || [];
  document.getElementById('artifacts-count').textContent = artifacts.length;
  const tbody = document.getElementById('artifacts-body');
  if (artifacts.length === 0) {
    tbody.innerHTML = '<tr><td colspan="3" class="empty">Sin artefactos</td></tr>';
    return;
  }
  tbody.innerHTML = artifacts.map(a => `
    <tr>
      <td><strong>${escapeHTML(a.target)}</strong></td>
      <td><span class="tag tag-${a.status === 'committed' ? 'success' : 'failed'}">${escapeHTML(a.status)}</span></td>
      <td style="font-size:12px">${(a.files || []).map(f => escapeHTML(f)).join('<br>') || '-'}</td>
    </tr>
  `).join('');
}

/* ---- Events ---- */
function renderEvents(events) {
  const list = events.events || [];
  document.getElementById('events-count').textContent = list.length;
  const tbody = document.getElementById('events-body');
  if (list.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty">Sin eventos</td></tr>';
    return;
  }
  tbody.innerHTML = list.map(e => `
    <tr onclick="showEventDetail('${escapeHTML(e.id)}')">
      <td>${e.sequence}</td>
      <td>${escapeHTML(e.topic)}</td>
      <td>${escapeHTML(e.source)}</td>
      <td>${formatTime(e.timestamp)}</td>
    </tr>
  `).join('');
}

/* ---- Sort ---- */
function sortTable(field) {
  if (sortField === field) {
    sortAsc = !sortAsc;
  } else {
    sortField = field;
    sortAsc = true;
  }
  const sorted = [...projectsCache].sort((a, b) => {
    const va = a[field] ?? '';
    const vb = b[field] ?? '';
    if (typeof va === 'string') {
      return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    }
    return sortAsc ? va - vb : vb - va;
  });
  renderProjects(sorted);
}

/* ---- Event Explorer ---- */
async function searchEvents() {
  const pid = currentProjectId;
  if (!pid) return;
  const topic = document.getElementById('expl-topic').value.trim();
  const source = document.getElementById('expl-source').value.trim();
  const search = document.getElementById('expl-search').value.trim();
  let url = '/api/events?project=' + encodeURIComponent(pid) + '&limit=50';
  if (topic) url += '&topic=' + encodeURIComponent(topic);
  if (source) url += '&source=' + encodeURIComponent(source);
  if (search) url += '&search=' + encodeURIComponent(search);
  try {
    const res = await fetch(url);
    const data = await res.json();
    renderExplorerResults(data.events || []);
  } catch (err) {
    document.getElementById('explorer-body').innerHTML =
      '<tr><td colspan="5" class="error-msg">Error: ' + escapeHTML(err.message) + '</td></tr>';
  }
}

function renderExplorerResults(events) {
  const tbody = document.getElementById('explorer-body');
  if (events.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty">Sin resultados</td></tr>';
    return;
  }
  tbody.innerHTML = events.map(e => `
    <tr onclick="showEventDetail('${escapeHTML(e.id)}')">
      <td>${e.sequence}</td>
      <td>${escapeHTML(e.topic)}</td>
      <td>${escapeHTML(e.source)}</td>
      <td>${formatTime(e.timestamp)}</td>
      <td><button class="explorer-btn-small" onclick="event.stopPropagation(); showEventDetail('${escapeHTML(e.id)}')">Ver</button></td>
    </tr>
  `).join('');
}

/* ---- Event Detail Modal ---- */
function showEventDetail(eventId) {
  fetch('/api/events/' + encodeURIComponent(eventId))
    .then(r => r.json())
    .then(data => {
      document.getElementById('event-detail-json').textContent =
        JSON.stringify(data, null, 2);
      document.getElementById('event-modal').style.display = 'flex';
    })
    .catch(err => {
      alert('Error al cargar evento: ' + err.message);
    });
}

function closeEventModal(event) {
  if (!event || event.target === document.getElementById('event-modal')) {
    document.getElementById('event-modal').style.display = 'none';
  }
}

/* ---- SSE Live Stream ---- */
function startLiveStream() {
  const pid = currentProjectId;
  if (!pid) return;
  if (eventSource) eventSource.close();
  document.getElementById('live-badge').style.display = 'inline-block';
  document.querySelector('.live-btn').style.display = 'none';
  document.querySelector('.stop-btn').style.display = 'inline-block';
  document.getElementById('live-counter').textContent = '0';

  eventSource = new EventSource('/api/events/live?project=' + encodeURIComponent(pid));
  eventSource.onmessage = (e) => {
    try {
      const evt = JSON.parse(e.data);
      const counter = document.getElementById('live-counter');
      counter.textContent = parseInt(counter.textContent || '0') + 1;
      // Prepend to explorer table
      const tbody = document.getElementById('explorer-body');
      if (tbody) {
        const firstChild = tbody.firstChild;
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${evt.sequence}</td>
          <td>${escapeHTML(evt.topic)}</td>
          <td>${escapeHTML(evt.source)}</td>
          <td>${formatTime(evt.timestamp)}</td>
          <td><button class="explorer-btn-small" onclick="showEventDetail('${escapeHTML(evt.id)}')">Ver</button></td>
        `;
        row.style.backgroundColor = '#2a3a5e';
        row.style.transition = 'background 2s';
        setTimeout(() => { row.style.backgroundColor = ''; }, 2000);
        tbody.insertBefore(row, firstChild);
        // Keep max 100 rows
        while (tbody.children.length > 100) {
          tbody.removeChild(tbody.lastChild);
        }
      }
    } catch (ex) {
      // ignore parse errors
    }
  };
  eventSource.onerror = () => {
    // Reconnect is automatic
  };
}

function stopLiveStream() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
  document.getElementById('live-badge').style.display = 'none';
  document.querySelector('.live-btn').style.display = 'inline-block';
  document.querySelector('.stop-btn').style.display = 'none';
}

/* ---- Helpers ---- */
function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatTime(ts) {
  if (!ts) return '-';
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
