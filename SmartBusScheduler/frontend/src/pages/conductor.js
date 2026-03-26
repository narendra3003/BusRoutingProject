// ============================================================
// PAGE: Conductor Dashboard  (/conductor/dashboard.js)
// Role: Conductor
// PURPOSE: Today's schedule, assigned trips, notifications
// ============================================================

// ── API Contracts ─────────────────────────────────────────────
//
// GET /api/conductor/dashboard
// HEADERS: Authorization: Bearer <conductor-token>
// OUTPUT:
// {
//   "conductor": { "id":"C-012","name":"R. Patel","badge":"C-4491" },
//   "today": "2024-03-10",
//   "shiftStart": "05:30",
//   "shiftEnd": "14:00",
//   "trips": [
//     { "id":"T-001","route":"Route 12A","bus":"BUS-101","driver":"J. Mehta",
//       "departure":"06:00","arrival":"08:30","status":"completed",
//       "passengersBoarded":210,"fareCollected":4200,
//       "stops":["Dadar","Andheri","Borivali"] },
//     { "id":"T-002","route":"Route 12A","bus":"BUS-101","driver":"J. Mehta",
//       "departure":"09:00","arrival":"11:30","status":"in-progress",
//       "passengersBoarded":87,"fareCollected":1740,
//       "stops":["Dadar","Andheri","Borivali"] }
//   ],
//   "totalPassengers": 297,
//   "totalFare": 5940,
//   "notifications": [
//     { "id":"N-1","type":"warning","message":"Overcrowding reported at Andheri stop","time":"09:55 AM","read":false }
//   ]
// }
//
// POST /api/conductor/fare-report
// INPUT:
// { "tripId":"T-002","passengersBoarded":120,"fareCollected":2400,"notes":"2 concession tickets" }
// OUTPUT: { "success":true, "message":"Fare report submitted for T-002" }
//
// PATCH /api/conductor/notifications/:id/read
// OUTPUT: { "success":true }
//
// ─────────────────────────────────────────────────────────────

// import { API } from "../shared/api.js";

let conductorData = null;
let reportingTripId = null;

function ConductorDashboard() {
async function loadConductorDashboard() {
  try {
    conductorData = await API.get("/conductor/dashboard");
    render(conductorData);
  } catch (err) {
    document.getElementById("root").innerHTML = `<div class="error-block">⚠ ${err.message}</div>`;
  }
}

async function submitFareReport(payload) {
  try {
    const res = await API.post("/conductor/fare-report", payload);
    if (res.success) {
      closeReportModal();
      await loadConductorDashboard();
      showToast(res.message);
    }
  } catch (err) { showToast("Error: " + err.message, "error"); }
}

async function markNotifRead(id) {
  try {
    await API.put(`/conductor/notifications/${id}/read`, {});
    const n = conductorData.notifications.find(x => x.id === id);
    if (n) { n.read = true; renderNotifPanel(); }
  } catch (err) { console.error(err); }
}

// ── Render ─────────────────────────────────────────────────────
function render(data) {
  document.getElementById("root").innerHTML = `
    <div class="conductor-page">
      <header class="cond-header">
        <div class="logo-mark">⬡ TRANSIT</div>
        <div class="cond-info">
          <div class="cond-name">${data.conductor.name}</div>
          <div class="cond-sub">CONDUCTOR · BADGE ${data.conductor.badge}</div>
        </div>
        <div class="header-stats">
          <div class="hstat">
            <div class="hstat-val">${data.totalPassengers}</div>
            <div class="hstat-label">PASSENGERS</div>
          </div>
          <div class="hstat">
            <div class="hstat-val">₹${data.totalFare.toLocaleString()}</div>
            <div class="hstat-label">FARE COLLECTED</div>
          </div>
          <div class="hstat">
            <div class="hstat-val">${data.shiftStart}–${data.shiftEnd}</div>
            <div class="hstat-label">SHIFT</div>
          </div>
        </div>
      </header>

      <div class="cond-layout">
        <section class="panel trips-section">
          <h2>ASSIGNED TRIPS — ${data.today}</h2>
          ${data.trips.map(t => conductorTripCard(t)).join("")}
        </section>

        <div class="right-col">
          <section class="panel" id="notifSection">
            <h2>NOTIFICATIONS</h2>
            ${notifList(data.notifications)}
          </section>
        </div>
      </div>

      <!-- Fare Report Modal -->
      <div id="reportModal" class="modal hidden">
        <div class="modal-box">
          <div class="modal-header">
            <span>SUBMIT FARE REPORT — <span id="reportTripId"></span></span>
            <button class="modal-close" onclick="closeReportModal()">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-grid">
              <div class="form-field">
                <label>PASSENGERS BOARDED</label>
                <input id="fr-passengers" type="number" min="0" placeholder="0" />
              </div>
              <div class="form-field">
                <label>FARE COLLECTED (₹)</label>
                <input id="fr-fare" type="number" min="0" placeholder="0" />
              </div>
              <div class="form-field full">
                <label>NOTES (optional)</label>
                <textarea id="fr-notes" rows="2" placeholder="Concessions, irregularities…"></textarea>
              </div>
            </div>
            <div class="form-actions">
              <button class="btn-secondary" onclick="closeReportModal()">CANCEL</button>
              <button class="btn-primary" onclick="handleFareSubmit()">SUBMIT REPORT</button>
            </div>
          </div>
        </div>
      </div>
      <div id="toast" class="toast hidden"></div>
    </div>
  `;
  attachConductorStyles();
}

function conductorTripCard(trip) {
  return `
    <div class="cond-trip-card status-${trip.status}">
      <div class="cond-trip-top">
        <span class="trip-id">${trip.id}</span>
        <span class="trip-route">${trip.route}</span>
        <span class="cond-status-badge ${trip.status}">${trip.status.toUpperCase()}</span>
      </div>
      <div class="cond-trip-meta">
        <span>🚌 ${trip.bus}</span>
        <span>👤 ${trip.driver}</span>
        <span>⏰ ${trip.departure} → ${trip.arrival}</span>
      </div>
      <div class="cond-trip-stops">${trip.stops.join(" → ")}</div>
      <div class="cond-trip-stats">
        <div class="cond-stat">
          <span class="cond-stat-val">${trip.passengersBoarded}</span>
          <span class="cond-stat-label">PASSENGERS</span>
        </div>
        <div class="cond-stat">
          <span class="cond-stat-val">₹${trip.fareCollected.toLocaleString()}</span>
          <span class="cond-stat-label">FARE</span>
        </div>
        ${trip.status === "in-progress" || trip.status === "completed" ? `
          <button class="btn-report" onclick="openReportModal('${trip.id}')">📋 FARE REPORT</button>
        ` : ""}
      </div>
    </div>
  `;
}

function notifList(notifications) {
  if (!notifications.length) return `<div class="empty">No notifications</div>`;
  return `<ul class="notif-list">${notifications.map(n => `
    <li class="notif-item ${n.read ? "read" : ""}" onclick="markNotifRead('${n.id}')">
      <span class="notif-type ${n.type}">${n.type.toUpperCase()}</span>
      <div class="notif-content"><div>${n.message}</div><div class="notif-time">${n.time}</div></div>
      ${!n.read ? '<span class="notif-dot"></span>' : ""}
    </li>`).join("")}</ul>`;
}

function renderNotifPanel() {
  const sec = document.getElementById("notifSection");
  if (sec && conductorData) sec.innerHTML = `<h2>NOTIFICATIONS</h2>${notifList(conductorData.notifications)}`;
}

function openReportModal(tripId) {
  reportingTripId = tripId;
  document.getElementById("reportTripId").textContent = tripId;
  document.getElementById("reportModal").classList.remove("hidden");
}

function closeReportModal() {
  document.getElementById("reportModal").classList.add("hidden");
  reportingTripId = null;
}

function handleFareSubmit() {
  const payload = {
    tripId: reportingTripId,
    passengersBoarded: parseInt(document.getElementById("fr-passengers").value) || 0,
    fareCollected: parseInt(document.getElementById("fr-fare").value) || 0,
    notes: document.getElementById("fr-notes").value,
  };
  submitFareReport(payload);
}

function showToast(msg, type = "success") {
  const t = document.getElementById("toast");
  t.textContent = msg; t.className = `toast ${type}`;
  setTimeout(() => t.classList.add("hidden"), 3000);
}

window.markNotifRead = markNotifRead;
window.openReportModal = openReportModal;
window.closeReportModal = closeReportModal;
window.handleFareSubmit = handleFareSubmit;

// ── Styles ─────────────────────────────────────────────────────
function attachConductorStyles() {
  if (document.getElementById("cond-styles")) return;
  const s = document.createElement("style");
  s.id = "cond-styles";
  s.textContent = `
    :root { --bg:#0b0c10; --surface:#13141a; --accent:#e8c84a; --green:#4adb8f; --red:#e84a6b; --blue:#4a9ee8; --text:#e0e0e0; --muted:#666; --border:#222; }
    * { box-sizing:border-box; margin:0; padding:0; }
    body { background:var(--bg); color:var(--text); font-family:'Courier New',monospace; }
    .conductor-page { padding:20px; max-width:1100px; margin:0 auto; }
    .cond-header { display:grid; grid-template-columns:auto auto 1fr; gap:20px; align-items:center; padding:16px 20px; background:var(--surface); border:1px solid var(--border); border-left:4px solid #4a9ee8; margin-bottom:20px; }
    .logo-mark { font-size:24px; color:var(--accent); }
    .cond-name { font-size:18px; font-weight:700; letter-spacing:2px; }
    .cond-sub { font-size:10px; color:var(--muted); letter-spacing:2px; }
    .header-stats { display:flex; gap:20px; justify-content:flex-end; }
    .hstat { text-align:center; }
    .hstat-val { font-size:20px; font-weight:700; color:var(--accent); }
    .hstat-label { font-size:8px; letter-spacing:2px; color:var(--muted); }
    .cond-layout { display:grid; grid-template-columns:1fr 300px; gap:16px; }
    .panel { background:var(--surface); border:1px solid var(--border); padding:20px; margin-bottom:16px; }
    .panel h2 { font-size:10px; letter-spacing:4px; color:var(--accent); margin-bottom:16px; padding-bottom:8px; border-bottom:1px solid var(--border); }
    .cond-trip-card { background:#0d0e12; border:1px solid var(--border); border-left:3px solid var(--muted); padding:16px; margin-bottom:12px; }
    .cond-trip-card.status-completed { border-left-color:var(--muted); }
    .cond-trip-card.status-in-progress { border-left-color:var(--green); }
    .cond-trip-card.status-upcoming { border-left-color:var(--blue); }
    .cond-trip-top { display:flex; align-items:center; gap:12px; margin-bottom:10px; }
    .trip-id { color:var(--accent); font-weight:700; }
    .trip-route { flex:1; }
    .cond-status-badge { font-size:9px; letter-spacing:1px; padding:3px 8px; }
    .cond-status-badge.completed { background:#1a1a1a; color:var(--muted); }
    .cond-status-badge.in-progress { background:#0d2e1a; color:var(--green); }
    .cond-status-badge.upcoming { background:#0d1f2e; color:var(--blue); }
    .cond-trip-meta { font-size:11px; color:var(--muted); margin-bottom:8px; display:flex; gap:16px; flex-wrap:wrap; }
    .cond-trip-stops { font-size:11px; color:var(--muted); margin-bottom:12px; }
    .cond-trip-stats { display:flex; align-items:center; gap:20px; }
    .cond-stat { text-align:center; }
    .cond-stat-val { font-size:18px; font-weight:700; color:var(--accent); display:block; }
    .cond-stat-label { font-size:8px; letter-spacing:2px; color:var(--muted); }
    .btn-report { margin-left:auto; padding:8px 14px; background:transparent; border:1px solid var(--accent); color:var(--accent); font-family:inherit; font-size:10px; letter-spacing:1px; cursor:pointer; }
    .btn-report:hover { background:var(--accent); color:#000; }
    .notif-list { list-style:none; }
    .notif-item { display:flex; align-items:flex-start; gap:8px; padding:10px 0; border-bottom:1px solid #111; cursor:pointer; }
    .notif-item.read { opacity:.5; }
    .notif-type { font-size:8px; letter-spacing:1px; padding:3px 6px; flex-shrink:0; }
    .notif-type.info { background:#0d1f2e; color:var(--blue); }
    .notif-type.warning { background:#2e2a0d; color:var(--accent); }
    .notif-content { flex:1; font-size:12px; }
    .notif-time { font-size:10px; color:var(--muted); margin-top:3px; }
    .notif-dot { width:6px; height:6px; background:var(--red); border-radius:50%; flex-shrink:0; margin-top:4px; }
    .btn-primary { padding:10px 20px; background:var(--accent); color:#000; font-family:inherit; font-size:11px; letter-spacing:2px; border:none; cursor:pointer; font-weight:700; }
    .btn-secondary { padding:10px 20px; background:transparent; color:var(--muted); font-family:inherit; font-size:11px; letter-spacing:2px; border:1px solid var(--border); cursor:pointer; }
    .modal { position:fixed; inset:0; background:rgba(0,0,0,.8); display:flex; align-items:center; justify-content:center; z-index:999; }
    .modal.hidden { display:none; }
    .modal-box { background:var(--surface); border:1px solid var(--accent); width:480px; max-width:95vw; }
    .modal-header { display:flex; justify-content:space-between; align-items:center; padding:16px 20px; border-bottom:1px solid var(--border); font-size:12px; letter-spacing:2px; }
    .modal-close { background:none; border:none; color:var(--muted); font-size:16px; cursor:pointer; }
    .modal-body { padding:20px; }
    .form-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:20px; }
    .form-field { display:flex; flex-direction:column; gap:6px; }
    .form-field.full { grid-column:1/-1; }
    .form-field label { font-size:9px; letter-spacing:2px; color:var(--muted); }
    .form-field input,.form-field textarea { background:#0d0e12; border:1px solid var(--border); color:var(--text); padding:10px; font-family:inherit; font-size:13px; resize:vertical; }
    .form-field input:focus,.form-field textarea:focus { outline:1px solid var(--accent); }
    .form-actions { display:flex; justify-content:flex-end; gap:10px; }
    .empty { text-align:center; color:var(--muted); padding:30px; font-size:12px; }
    .error-block { padding:40px; text-align:center; color:var(--red); }
    .toast { position:fixed; bottom:24px; right:24px; padding:12px 20px; background:var(--green); color:#000; font-size:12px; font-family:'Courier New',monospace; }
    .toast.error { background:var(--red); color:#fff; }
    .toast.hidden { display:none; }
    @media(max-width:800px) { .cond-layout{grid-template-columns:1fr} .cond-header{grid-template-columns:auto 1fr} .header-stats{grid-column:1/-1;justify-content:flex-start} }
  `;
  document.head.appendChild(s);
}

document.addEventListener("DOMContentLoaded", loadConductorDashboard);
}
export default ConductorDashboard();
