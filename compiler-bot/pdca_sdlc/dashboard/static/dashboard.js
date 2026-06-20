/* PDCA-sdlc Dashboard — Frontend logic (vanilla JS, 0 dependencies) */

/* ---- State ---- */
let projectsCache = [];
let sortField = null;
let sortAsc = true;

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
    const [projRes, agentsRes, eventsRes] = await Promise.all([
      fetch('/api/projects'),
      fetch('/api/agents'),
      fetch('/api/events?project=_all&limit=1'),
    ]);
    const projects = await projRes.json();
    const agents = await agentsRes.json();
    // get total events from first project or empty
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

    renderProjects(projectsCache);
  } catch (err) {
    document.getElementById('projects-body').innerHTML =
      '<tr><td colspan="5" class="error-msg">Error al cargar: ' + escapeHTML(err.message) + '</td></tr>';
  } finally {
    showLoading(false);
  }
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
  showLoading(true);
  try {
    const [projRes, traceRes, eventsRes] = await Promise.all([
      fetch('/api/projects/' + encodeURIComponent(projectId)),
      fetch('/api/projects/' + encodeURIComponent(projectId) + '/trace'),
      fetch('/api/events?project=' + encodeURIComponent(projectId) + '&limit=20'),
    ]);
    const project = await projRes.json();
    const trace = await traceRes.json();
    const events = await eventsRes.json();

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
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    showLoading(false);
  }
}

function showDashboard() {
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
  let indent = 0;
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];
    const cls = n.type;
    const label = n.id;
    const isLast = i === nodes.length - 1;
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
    <tr>
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
