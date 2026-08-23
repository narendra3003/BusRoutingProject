import { useState, useRef, useEffect, useMemo } from "react";
import {
  MapContainer,
  TileLayer,
  Polyline,
  CircleMarker,
  Popup,
  useMap
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

function addMinutes(time, mins) {
  const [h, m] = time.split(":").map(Number);
  const total = h * 60 + m + mins;
  return `${String(Math.floor(total / 60) % 24).padStart(2, "0")}:${String(
    total % 60
  ).padStart(2, "0")}`;
}
function timeToMinutes(time) {
  const [h, m] = time.split(":").map(Number);
  return h * 60 + m;
}
function getTodayKey() {
  const day = new Date().getDay();

  // 0 = Sunday
  if (day === 0) return "sun";

  // 6 = Saturday
  if (day === 6) return "sat";

  return "weekday";
}

function getTodayLabel() {
  const days = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday"
  ];

  return days[new Date().getDay()];
}

function FitBounds({ coords }) {
  const map = useMap();

  useEffect(() => {
    if (coords?.length) {
      map.fitBounds(coords, { padding: [52, 52] });
    }
  }, [coords, map]);

  return null;
}

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=DM+Mono:wght@400;500&display=swap');

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Nunito', sans-serif;
  background: #f4f6f9;
}

/* HERO */
.hero {
  background: #0C447C;
  padding: 72px 24px 0;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero-title {
  font-size: clamp(36px,5vw,58px);
  font-weight: 900;
  color: #fff;
  line-height: 1.15;
  letter-spacing: -1px;
  margin-bottom: 16px;
}

.hero-title .highlight {
  color: #b5cee6;
}

.hero-sub {
  font-size: 16px;
  color: rgba(255,255,255,0.85);
  margin-bottom: 48px;
}

.search-outer {
  max-width: 660px;
  margin: 0 auto 20px;
  position: relative;
  z-index: 20;
}

.search-bar {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 50px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.14);
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-family: 'Nunito', sans-serif;
  font-size: 15px;
  color: #1a1c20;
  padding: 18px 0 18px 22px;
  background: transparent;
}

.search-input::placeholder {
  color: #a0b6e2;
}

.find-btn {
  background: #0f3966;
  color: #fff;
  border: none;
  border-radius: 50px;
  padding: 13px 28px;
  margin: 6px;
  font-family: 'Nunito', sans-serif;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s, transform 0.1s;
  flex-shrink: 0;
}

.find-btn:hover {
  background: #0d447b;
  transform: scale(1.02);
}

/* BUS STRIP */
.bus-strip {
  width: 100%;
  display: block;
  margin-top: 28px;
  position: relative;
  z-index: 5;
  line-height: 0;
}

.bus-strip svg {
  display: block;
  width: 100%;
}

@keyframes dashMove {
  from { stroke-dashoffset: 0; }
  to   { stroke-dashoffset: -40; }
}

@keyframes stopPulse {
  0%,100% { opacity: 0.55; }
  50%     { opacity: 1; }
}

@keyframes stopRing {
  0%   { r: 5; opacity: 0.65; }
  100% { r: 14; opacity: 0; }
}

@keyframes headlight {
  0%,100% { opacity: 0.45; }
  50%     { opacity: 0.8; }
}

.bus-strip .dash-anim {
  animation: dashMove 1.2s linear infinite;
}

.bus-strip .stop-pulse {
  animation: stopPulse 2s ease-in-out infinite;
}

.bus-strip .stop-ring {
  fill: none;
  stroke: rgba(255,255,255,0.45);
  stroke-width: 1.2;
  animation: stopRing 2.2s ease-out infinite;
}

.bus-strip .headlight {
  animation: headlight 1.4s ease-in-out infinite;
}

.dropdown {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  right: 0;
  background: #E6F1FB;
  border-radius: 18px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.14);
  overflow: hidden;
  z-index: 100;
  animation: fadeDown 0.15s ease;
}

@keyframes fadeDown {
  from {
    opacity:0;
    transform:translateY(-8px);
  }

  to {
    opacity:1;
    transform:translateY(0);
  }
}

.dd-item {
  display: flex;
  flex-direction: column;
  padding: 10px 18px;
  cursor: pointer;
  transition: background 0.1s;
}

.dd-item:hover {
  background: #f5f3ff;
}

.dd-text-main {
  font-size: 13px;
  font-weight: 700;
  color: #1a1c20;
}

.dd-no-result {
  padding: 20px;
  text-align: center;
  font-size: 13px;
  color: #aab0bc;
}

.body-layout {
  display: flex;
  gap: 24px;
  max-width: 1280px;
  margin: 40px auto 60px;
  padding: 0 24px;
  align-items: flex-start;
}

.left-panel {
  width: 320px;
  flex-shrink: 0;
}

.panel-heading {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #aab0bc;
  margin-bottom: 14px;
}

.route-header-card {
  background: #E6F1FB;
  border-radius: 16px;
  padding: 16px 18px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  border: 1.5px solid #f0f2f5;
}

.rhc-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rhc-badge {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-family: 'DM Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  background: #f4f6f9;
}

.rhc-info {
  flex: 1;
  min-width: 0;
}

.rhc-name {
  font-size: 14px;
  font-weight: 800;
  color: #1a1c20;
}

.rhc-path {
  font-size: 11px;
  color: #8a8f9a;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rhc-meta {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f0f2f5;
  flex-wrap: wrap;
  align-items: center;
}

.rhc-tag {
  font-size: 10px;
  font-family: 'DM Mono', monospace;
  font-weight: 500;
  background: #f4f6f9;
  color: #6b7280;
  padding: 3px 8px;
  border-radius: 5px;
}

.sched-btn {
  margin-left: auto;
  background: #f4f6f9;
  color: #374151;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 11px;
  font-weight: 700;
  font-family: 'Nunito', sans-serif;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
}

.sched-btn:hover {
  background: #e9eaec;
}

.empty-state {
  background: #fff;
  border-radius: 16px;
  padding: 40px 20px;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.055);
}

.empty-text {
  font-size: 13px;
  font-weight: 700;
  color: #c8cdd6;
  margin-bottom: 4px;
}

.map-panel {
  flex: 1;
  min-width: 0;
  position: sticky;
  top: 24px;
}

.map-card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.map-card-title {
  font-size: 14px;
  font-weight: 800;
  color: #1a1c20;
}

.map-card-sub {
  font-size: 11px;
  color: #aab0bc;
  margin-top: 2px;
  font-family: 'DM Mono', monospace;
}

.map-placeholder {
  height: 500px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #fafbfc;
}

.map-ph-text {
  font-size: 15px;
  font-weight: 700;
  color: #c8cdd6;
}

.map-ph-sub {
  font-size: 12px;
  color: #d4d8df;
}

.leaflet-container {
  height: 500px !important;
  width: 100% !important;
}

.leaflet-popup-content-wrapper {
  border-radius: 12px !important;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(15,17,22,0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.modal {
  background: #fff;
  border-radius: 24px;
  width: 100%;
  max-width: 820px;
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 24px 80px rgba(0,0,0,0.2);
}

.modal-head {
  padding: 24px 24px 0;
  flex-shrink: 0;
}

.modal-head-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.modal-route-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-badge-pill {
  padding: 6px 16px;
  border-radius: 20px;
  font-family: 'DM Mono', monospace;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
}

.modal-route-name {
  font-size: 20px;
  font-weight: 900;
  color: #1a1c20;
  line-height: 1.2;
}

.modal-route-path {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 2px;
}

.modal-close {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #f3f4f6;
  border: none;
  font-size: 16px;
  color: #6b7280;
  cursor: pointer;
}

.modal-day-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
  padding: 8px 14px;
  border-radius: 14px;
  font-size: 12px;
  font-weight: 800;
  margin-bottom: 18px;
}

.modal-divider {
  height: 1px;
  background: #f3f4f6;
}

.sched-grid-wrap {
  flex: 1;
  overflow: auto;
}

.sched-table {
  display: table;
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
}

.sched-thead {
  display: table-header-group;
}

.sched-tr-head {
  display: table-row;
}

.sched-th-stop {
  display: table-cell;
  position: sticky;
  left: 0;
  z-index: 3;
  width: 148px;
  min-width: 148px;
  padding: 11px 12px 11px 24px;
  background: #fafafa;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #9ca3af;
  border-right: 1px solid #f0f2f5;
  border-bottom: 2px solid #f0f2f5;
}

.sched-th-trips {
  display: table-cell;
  padding: 11px 16px;
  background: #fff;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #9ca3af;
  border-bottom: 2px solid #f0f2f5;
  white-space: nowrap;
}

.sched-count-pill {
  display: inline-block;
  background: #f3f4f6;
  color: #9ca3af;
  font-size: 10px;
  font-family: 'DM Mono', monospace;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: none;
  letter-spacing: 0;
  margin-left: 6px;
}

.sched-tbody {
  display: table-row-group;
}

.sched-tr {
  display: table-row;
}

.sched-td-stop {
  display: table-cell;
  position: sticky;
  left: 0;
  z-index: 2;
  width: 148px;
  min-width: 148px;
  padding: 14px 12px 14px 24px;
  background: #fafafa;
  border-right: 1px solid #f0f2f5;
  border-bottom: 1px solid #f3f4f6;
}

.sched-stop-inner {
  display: flex;
  align-items: center;
  gap: 9px;
}

.sched-stop-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  border: 2px solid;
  background: #fff;
  flex-shrink: 0;
}

.sched-stop-name {
  font-size: 12px;
  font-weight: 700;
  color: #1a1c20;
  white-space: nowrap;
}

.sched-td-times {
  display: table-cell;
  padding: 14px 16px;
  border-bottom: 1px solid #f3f4f6;
}

.sched-times-inner {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
}

.sched-time-pill {
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  font-weight: 500;
  color: #374151;
  background: #f8f9fb;
  border-radius: 7px;
  padding: 5px 8px;
  border: 1px solid #eef0f3;
}

.no-service-msg {
  padding: 52px;
  text-align: center;
  color: #d1d5db;
  font-size: 13px;
  font-weight: 600;
}
`;

/* ───────────────── BUS ANIMATION ───────────────── */

function BusAnimation() {
  return (
    <div className="bus-strip">
      <svg
        viewBox="0 0 700 100"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
      >
        <defs>
          <path
            id="heroRoute"
            d="M 10 75
               C 90 75 120 28 205 28
               C 290 28 318 75 405 66
               C 465 59 498 18 582 18
               C 630 18 660 36 695 52"
          />
        </defs>

        <use
          href="#heroRoute"
          fill="none"
          stroke="rgba(255,255,255,0.12)"
          strokeWidth="2.5"
          strokeLinecap="round"
        />

        <use
          href="#heroRoute"
          fill="none"
          stroke="rgba(255,255,255,0.72)"
          strokeWidth="2"
          strokeDasharray="8 14"
          strokeLinecap="round"
          className="dash-anim"
        />

        {[
          { cx: 10, cy: 75, delay: "0s" },
          { cx: 205, cy: 28, delay: "0.6s" },
          { cx: 405, cy: 66, delay: "1.2s" },
          { cx: 582, cy: 18, delay: "1.8s" }
        ].map(({ cx, cy, delay }, i) => (
          <g key={i}>
            <circle
              cx={cx}
              cy={cy}
              r="5"
              className="stop-ring"
              style={{ animationDelay: delay }}
            />
            <circle
              cx={cx}
              cy={cy}
              r="5"
              fill="none"
              stroke="rgba(255,255,255,0.5)"
              strokeWidth="1.4"
            />
            <circle
              cx={cx}
              cy={cy}
              r="2.8"
              fill="white"
              className="stop-pulse"
              style={{ animationDelay: delay }}
            />
          </g>
        ))}

        <g>
          <animateMotion
            dur="7s"
            repeatCount="indefinite"
            rotate="auto"
          >
            <mpath href="#heroRoute" />
          </animateMotion>

          <rect
            x="-17"
            y="-9"
            width="34"
            height="18"
            rx="3.5"
            fill="white"
            opacity="0.95"
          />
        </g>
      </svg>
    </div>
  );
}

/* ───────────────── SCHEDULE MODAL ───────────────── */

function ScheduleModal({ route, onClose }) {
  const todayKey = getTodayKey();
  const todayLabel = getTodayLabel();
  const now = new Date();

  const currentMinutes =
    now.getHours() * 60 + now.getMinutes();
  const baseTimes = useMemo(() => {
    return route?.timetable?.[todayKey] || [];
  }, [route, todayKey]);

  useEffect(() => {
    const fn = (e) => {
      if (e.key === "Escape") onClose();
    };

    window.addEventListener("keydown", fn);

    return () => window.removeEventListener("keydown", fn);
  }, [onClose]);

  return (
    <div
      className="modal-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="modal">
        <div className="modal-head">
          <div className="modal-head-top">
            <div className="modal-route-info">
              <div
                className="modal-badge-pill"
                style={{ background: route.color }}
              >
                {route.id}
              </div>

              <div>
                <div className="modal-route-name">
                  {route.name}
                </div>

                <div className="modal-route-path">
                  {route.from_stop} → {route.to_stop}
                </div>
              </div>
            </div>

            <button className="modal-close" onClick={onClose}>
              ✕
            </button>
          </div>

          {/* TODAY ONLY */}
          <div className="modal-day-badge">
            📅 Today's Schedule • {todayLabel}
          </div>

          <div className="modal-divider" />
        </div>

        <div className="sched-grid-wrap">
          {baseTimes.length === 0 ? (
            <div className="no-service-msg">
              No service available today
            </div>
          ) : (
            <div className="sched-table">
              <div className="sched-thead">
                <div className="sched-tr-head">
                  <div className="sched-th-stop">
                    Stop
                  </div>

                  <div className="sched-th-trips">
                    Today's Trips
                    <span className="sched-count-pill">
                      {baseTimes.length} departures
                    </span>
                  </div>
                </div>
              </div>

              <div className="sched-tbody">
                {route.stops.map((stop, si) => {
                  const times = baseTimes
                  .map((t) => addMinutes(t, route.stopOffsets[si]))
                  .sort((a, b) => timeToMinutes(a) - timeToMinutes(b));

                  const isFirst = si === 0;
                  const isLast = si === route.stops.length - 1;

                  return (
                    <div key={stop} className="sched-tr">
                      <div className="sched-td-stop">
                        <div className="sched-stop-inner">
                          <div
                            className="sched-stop-dot"
                            style={{
                              borderColor: route.color,
                              background:
                                isFirst || isLast
                                  ? route.color
                                  : "#fff"
                            }}
                          />

                          <span className="sched-stop-name">
                            {stop}
                          </span>
                        </div>
                      </div>

                      <div className="sched-td-times">
                        <div className="sched-times-inner">
                          {times.map((t, ti) => {
                            const isPast =
                              timeToMinutes(t) < currentMinutes;

                            return (
                              <span
                                key={ti}
                                className="sched-time-pill"
                                style={{
                                  background: isPast
                                    ? "#d1d5db"
                                    : "#eff6ff",

                                  color: isPast
                                    ? "#6b7280"
                                    : "#1d4ed8",

                                  border: isPast
                                    ? "1px solid #c4c7cc"
                                    : "1px solid #bfdbfe",

                                  opacity: isPast ? 0.7 : 1
                                }}
                              >
                                {t}
                              </span>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ───────────────── MAIN ───────────────── */

export default function CustomerPage() {
  const [routes, setRoutes] = useState([]);
  const [stops, setStops] = useState([]);
  const [loading, setLoading] = useState(true);

  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);

  const [activeRoute, setActiveRoute] = useState(null);
  const [selectedStop, setSelectedStop] = useState(null);

  const [scheduleRoute, setScheduleRoute] = useState(null);

  const inputRef = useRef(null);

  useEffect(() => {
    fetch("http://localhost:8000/public/custRoutes")
      .then((r) => r.json())
      .then((d) => setRoutes(Array.isArray(d) ? d : []))
      .catch(() => setRoutes([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetch("http://localhost:8000/stops")
      .then((r) => r.json())
      .then((d) => setStops(Array.isArray(d) ? d : []))
      .catch(() => setStops([]));
  }, []);

  const fetchRouteById = async (id) => {
    try {
      const data = await fetch(
        `http://localhost:8000/public/cust_routes/${id}`
      ).then((r) => r.json());

      setRoutes((prev) =>
        prev.find((r) => r.id === id)
          ? prev.map((r) => (r.id === id ? data : r))
          : [...prev, data]
      );

      return data;
    } catch {
      return null;
    }
  };

  const fetchRoutesByStop = async (stopId) => {
    try {
      const data = await fetch(
        `http://localhost:8000/public/cust-routes-by-stop?stop_id=${stopId}`
      ).then((r) => r.json());

      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  };

  const SUGGESTIONS = [
    ...routes.map((r) => ({
      type: "route",
      id: r.id,
      label: `Route ${r.id} – ${r.from_stop} to ${r.to_stop}`
    })),

    ...stops.map((s) => ({
      type: "stop",
      id: s.id,
      label: s.name
    }))
  ];

  const filtered = SUGGESTIONS.filter((s) =>
    s.label.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = async (s) => {
    if (s.type === "route") {
      setActiveRoute(s.id);

      const route = await fetchRouteById(s.id);

      setScheduleRoute(route);
    } else {
      setQuery(s.label);

      setSelectedStop(s.id);

      setRoutes(await fetchRoutesByStop(s.id));
    }
  };

  const currentRoute = routes.find((r) => r.id === activeRoute);

  return (
    <>
      <style>{CSS}</style>

      {scheduleRoute && (
        <ScheduleModal
          route={scheduleRoute}
          onClose={() => setScheduleRoute(null)}
        />
      )}

      {/* HERO */}
      <div className="hero">
        <h1 className="hero-title">
          Find your <span className="highlight">route</span>,
          <br />
          reach on time.
        </h1>

        <p className="hero-sub">
          Search any bus number, route name, or stop
        </p>

        <div className="search-outer">
          <div className="search-bar">
            <input
              ref={inputRef}
              className="search-input"
              placeholder="Search route / stop..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setTimeout(() => setFocused(false), 180)}
            />

            {query && (
              <button
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: "0 10px"
                }}
                onClick={() => setQuery("")}
              >
                ×
              </button>
            )}

            <button className="find-btn">
              Find →
            </button>
          </div>

          {focused && (
            <div className="dropdown">
              {filtered.length === 0 && (
                <div className="dd-no-result">
                  No results
                </div>
              )}

              {filtered.map((s) => (
                <div
                  key={s.id}
                  className="dd-item"
                  onMouseDown={() => handleSelect(s)}
                >
                  <div className="dd-text-main">
                    {s.label}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <BusAnimation />
      </div>

      {/* BODY */}
      <div className="body-layout">
        <div className="left-panel">
          <div className="panel-heading">
            {query
              ? `Results for "${query}"`
              : "All Routes"} — {routes.length}
          </div>

          {loading ? (
            <div className="empty-state">
              <div className="empty-text">
                Loading...
              </div>
            </div>
          ) : routes.length === 0 ? (
            <div className="empty-state">
              <div className="empty-text">
                No routes found
              </div>
            </div>
          ) : (
            routes.map((r) => (
              <div
                key={r.id}
                className="route-header-card"
                onClick={() => setActiveRoute(r.id)}
                style={{
                  cursor: "pointer",
                  border:
                    activeRoute === r.id
                      ? "1.5px solid #d1d5db"
                      : "1.5px solid #f0f2f5"
                }}
              >
                <div className="rhc-top">
                  <div className="rhc-badge">
                    {r.id}
                  </div>

                  <div className="rhc-info">
                    <div className="rhc-name">
                      {r.name}
                    </div>

                    <div className="rhc-path">
                      {r.from_stop} → {r.to_stop}
                    </div>
                  </div>
                </div>

                <div className="rhc-meta">
                  <span className="rhc-tag">
                    {r.stops?.length || 0} stops
                  </span>

                  <button
                    className="sched-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      setScheduleRoute(r);
                    }}
                  >
                    Today's Schedule →
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="map-panel">
          <div className="map-card">
            <div className="map-card-header">
              <div>
                <div className="map-card-title">
                  {currentRoute
                    ? `Route ${currentRoute.id} – ${currentRoute.name}`
                    : "Route Viewer"}
                </div>

                <div className="map-card-sub">
                  {currentRoute
                    ? `${currentRoute.from_stop} → ${currentRoute.to_stop}`
                    : "Select a route to view"}
                </div>
              </div>
            </div>

            {currentRoute ? (
              <MapContainer
                center={
                  currentRoute.coords?.[0] || [19.076, 72.8777]
                }
                zoom={12}
              >
                <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" />

                {currentRoute.coords && (
                  <>
                    <FitBounds coords={currentRoute.coords} />

                    <Polyline
                      positions={currentRoute.coords}
                      pathOptions={{
                        color:
                          currentRoute.color || "#2563eb",
                        weight: 5
                      }}
                    />
                  </>
                )}

                {currentRoute.coords?.map((pos, i) => (
                  <CircleMarker
                    key={i}
                    center={pos}
                    radius={7}
                  >
                    <Popup>
                      <div className="popup-stop">
                        {currentRoute.stops?.[i]}
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </MapContainer>
            ) : (
              <div className="map-placeholder">
                <div className="map-ph-text">
                  No route selected
                </div>

                <div className="map-ph-sub">
                  Pick a route to see it on map
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}