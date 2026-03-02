import { useState, useRef, useEffect } from "react";
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// ─── Data ────────────────────────────────────────────────────────────────────

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const ROUTES = [
  {
    id: "101", name: "Green Express", color: "#1d6ef5",
    from: "Connaught Place", to: "Shastri Nagar",
    stops: ["Connaught Place", "Karol Bagh", "Patel Nagar", "Shastri Nagar"],
    coords: [[28.6315,77.2167],[28.6512,77.1904],[28.6519,77.1711],[28.6694,77.1916]],
    liveStop: "Patel Nagar",
    etaFromLive: { "Shastri Nagar": 8 },
    stopOffsets: [0, 7, 14, 20],
    timetable: {
      weekday: ["06:00","06:08","06:16","06:24","06:32","06:40","07:00","07:08","07:16","07:24","07:32","07:40","08:00","08:08","08:16","08:24","08:32","08:40","09:00","09:15","09:30","09:45","10:00","10:20","10:40","11:00","11:20","11:40","12:00","12:20","12:40","13:00","13:20","13:40","14:00","14:20","14:40","15:00","15:20","15:40","16:00","16:08","16:16","16:24","16:32","16:40","17:00","17:08","17:16","17:24","17:32","17:40","18:00","18:15","18:30","18:45","19:00","19:20","19:40","20:00","20:30","21:00","21:30","22:00"],
      sat:     ["07:00","07:20","07:40","08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30","12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30","16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30","20:00","20:30","21:00","21:30","22:00"],
      sun:     ["08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30","12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30","16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30","20:00","20:30","21:00","21:30","22:00"],
    },
  },
  {
    id: "202", name: "City Rider", color: "#2563eb",
    from: "India Gate", to: "Hauz Khas",
    stops: ["India Gate", "Khan Market", "AIIMS", "Hauz Khas"],
    coords: [[28.6129,77.2295],[28.6005,77.2273],[28.5672,77.2100],[28.5494,77.2017]],
    liveStop: "AIIMS",
    etaFromLive: { "Hauz Khas": 10 },
    stopOffsets: [0, 8, 16, 24],
    timetable: {
      weekday: ["06:15","06:30","06:45","07:00","07:15","07:30","07:45","08:00","08:15","08:30","08:45","09:00","09:20","09:40","10:00","10:20","10:40","11:00","11:20","11:40","12:00","12:20","12:40","13:00","13:30","14:00","14:30","15:00","15:30","16:00","16:15","16:30","16:45","17:00","17:15","17:30","17:45","18:00","18:20","18:40","19:00","19:30","20:00","20:30","21:00","21:30","22:00"],
      sat:     ["07:30","08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30","12:00","12:30","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00"],
      sun:     ["09:00","09:30","10:00","10:30","11:00","11:30","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00"],
    },
  },
  {
    id: "303", name: "Metro Link", color: "#3b82f6",
    from: "Kashmere Gate", to: "Azadpur",
    stops: ["Kashmere Gate", "Civil Lines", "Model Town", "Azadpur"],
    coords: [[28.6673,77.2300],[28.6822,77.2287],[28.7073,77.1925],[28.7090,77.1772]],
    liveStop: "Model Town",
    etaFromLive: { "Azadpur": 7 },
    stopOffsets: [0, 6, 12, 18],
    timetable: {
      weekday: ["06:30","06:45","07:00","07:15","07:30","07:45","08:00","08:15","08:30","08:45","09:00","09:20","09:40","10:00","10:20","10:40","11:00","11:20","11:40","12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30","16:00","16:15","16:30","16:45","17:00","17:15","17:30","17:45","18:00","18:20","18:40","19:00","19:30","20:00","20:30","21:00","22:00"],
      sat:     ["08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00"],
      sun:     ["09:00","09:30","10:00","10:30","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00"],
    },
  },
  {
    id: "404", name: "Rapid Route", color: "#1e40af",
    from: "Lajpat Nagar", to: "Govindpuri",
    stops: ["Lajpat Nagar", "Nehru Place", "Kalkaji", "Govindpuri"],
    coords: [[28.5623,77.2433],[28.5499,77.2522],[28.5389,77.2586],[28.5301,77.2619]],
    liveStop: "Kalkaji",
    etaFromLive: { "Govindpuri": 8 },
    stopOffsets: [0, 5, 10, 16],
    timetable: {
      weekday: ["05:45","06:00","06:10","06:20","06:30","06:40","06:50","07:00","07:10","07:20","07:30","07:40","07:50","08:00","08:10","08:20","08:30","08:40","08:50","09:00","09:15","09:30","09:45","10:00","10:20","10:40","11:00","11:30","12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30","16:00","16:10","16:20","16:30","16:40","16:50","17:00","17:10","17:20","17:30","17:40","17:50","18:00","18:15","18:30","18:45","19:00","19:30","20:00","20:30","21:00","21:30","22:00","22:30"],
      sat:     ["07:00","07:30","08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30","12:00","12:30","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00"],
      sun:     ["08:00","08:30","09:00","09:30","10:00","10:30","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00"],
    },
  },
  {
    id: "505", name: "Capital Cruiser", color: "#60a5fa",
    from: "Rajouri Garden", to: "Shalimar Bagh",
    stops: ["Rajouri Garden", "Punjabi Bagh", "Ashok Vihar", "Shalimar Bagh"],
    coords: [[28.6412,77.1197],[28.6663,77.1347],[28.6826,77.1652],[28.7067,77.1709]],
    liveStop: "Ashok Vihar",
    etaFromLive: { "Shalimar Bagh": 9 },
    stopOffsets: [0, 8, 16, 23],
    timetable: {
      weekday: ["06:00","06:20","06:40","07:00","07:20","07:40","08:00","08:20","08:40","09:00","09:30","10:00","10:30","11:00","11:30","12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30","16:00","16:20","16:40","17:00","17:20","17:40","18:00","18:20","18:40","19:00","19:30","20:00","20:30","21:00","21:30","22:00"],
      sat:     ["08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00"],
      sun:     ["09:00","09:30","10:00","10:30","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00"],
    },
  },
];

function addMinutes(time, mins) {
  const [h, m] = time.split(":").map(Number);
  const total = h * 60 + m + mins;
  return `${String(Math.floor(total / 60) % 24).padStart(2,"0")}:${String(total % 60).padStart(2,"0")}`;
}

function getDayKey(dayLabel) {
  if (dayLabel === "Sat") return "sat";
  if (dayLabel === "Sun") return "sun";
  return "weekday";
}

const ALL_STOPS = [...new Set(ROUTES.flatMap(r => r.stops))];
const SUGGESTIONS = [
  ...ROUTES.map(r => ({ type: "route", id: r.id, label: `Route ${r.id} – ${r.from} to ${r.to}`, sub: "", data: r })),
  ...ALL_STOPS.map(s => ({ type: "stop", id: s, label: s, sub: `Routes: ${ROUTES.filter(r => r.stops.includes(s)).map(r => r.id).join(", ")}` })),
];
const QUICK_CHIPS = ["101", "AIIMS", "Kashmere Gate", "404"];

function FitBounds({ coords }) {
  const map = useMap();
  useEffect(() => {
    if (coords?.length) map.fitBounds(coords, { padding: [52, 52] });
  }, [coords, map]);
  return null;
}

// ─── CSS ─────────────────────────────────────────────────────────────────────

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=DM+Mono:wght@400;500&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Nunito', sans-serif; background: #f4f6f9; }

.hero { background: #1db954; padding: 72px 24px 80px; text-align: center; }
.hero-title { font-size: clamp(36px,5vw,58px); font-weight: 900; color: #fff; line-height: 1.15; letter-spacing: -1px; margin-bottom: 16px; }
.hero-title .highlight { color: #0a4d25; }
.hero-sub { font-size: 16px; color: rgba(255,255,255,0.85); margin-bottom: 48px; }

.search-outer { max-width: 660px; margin: 0 auto 20px; position: relative; z-index: 20; }
.search-bar { display: flex; align-items: center; background: #fff; border-radius: 50px; box-shadow: 0 8px 32px rgba(0,0,0,0.14); }
.search-input { flex: 1; border: none; outline: none; font-family: 'Nunito', sans-serif; font-size: 15px; color: #1a1c20; padding: 18px 0 18px 22px; background: transparent; }
.search-input::placeholder { color: #aab0bc; }
.find-btn { background: #1db954; color: #fff; border: none; border-radius: 50px; padding: 13px 28px; margin: 6px; font-family: 'Nunito', sans-serif; font-size: 14px; font-weight: 700; cursor: pointer; white-space: nowrap; transition: background 0.15s, transform 0.1s; flex-shrink: 0; }
.find-btn:hover { background: #17a347; transform: scale(1.02); }

.dropdown { position: absolute; top: calc(100% + 10px); left: 0; right: 0; background: #fff; border-radius: 18px; box-shadow: 0 12px 40px rgba(0,0,0,0.14); overflow: hidden; z-index: 100; animation: fadeDown 0.15s ease; }
@keyframes fadeDown { from { opacity:0; transform:translateY(-8px); } to { opacity:1; transform:translateY(0); } }
.dd-section + .dd-section { border-top: 1px solid #f0f2f5; }
.dd-section-label { font-size: 10px; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase; color: #aab0bc; padding: 10px 18px 4px; }
.dd-item { display: flex; flex-direction: column; padding: 10px 18px; cursor: pointer; transition: background 0.1s; }
.dd-item:hover { background: #f4faf7; }
.dd-text-main { font-size: 13px; font-weight: 700; color: #1a1c20; }
.dd-text-sub { font-size: 11px; color: #aab0bc; margin-top: 1px; font-family: 'DM Mono', monospace; }
.dd-no-result { padding: 20px; text-align: center; font-size: 13px; color: #aab0bc; }

.chips-row { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 8px; }
.chip { background: rgba(255,255,255,0.18); color: #fff; border: 1.5px solid rgba(255,255,255,0.35); border-radius: 20px; padding: 6px 16px; font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.15s; }
.chip:hover { background: rgba(255,255,255,0.32); }

.body-layout { display: flex; gap: 24px; max-width: 1280px; margin: 40px auto 60px; padding: 0 24px; align-items: flex-start; }

.left-panel { width: 320px; flex-shrink: 0; }
.panel-heading { font-size: 11px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: #aab0bc; margin-bottom: 14px; }

.route-tabs { display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap; }
.rtab { display: flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; cursor: pointer; border: 1.5px solid #e8eaed; background: #fff; color: #8a8f9a; font-family: 'Nunito', sans-serif; transition: all 0.15s; }
.rtab:hover { border-color: #d1d5db; color: #374151; }
.rtab.active { color: #fff; background: #374151; border-color: #374151; }

.route-header-card { background: #fff; border-radius: 16px; padding: 16px 18px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.07); border: 1.5px solid #f0f2f5; }
.rhc-top { display: flex; align-items: center; gap: 12px; }
.rhc-badge { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 600; color: #6b7280; background: #f4f6f9; }
.rhc-info { flex: 1; min-width: 0; }
.rhc-name { font-size: 14px; font-weight: 800; color: #1a1c20; }
.rhc-path { font-size: 11px; color: #8a8f9a; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rhc-meta { display: flex; gap: 8px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f0f2f5; flex-wrap: wrap; align-items: center; }
.rhc-tag { font-size: 10px; font-family: 'DM Mono', monospace; font-weight: 500; background: #f4f6f9; color: #6b7280; padding: 3px 8px; border-radius: 5px; }
.sched-btn { margin-left: auto; background: #f4f6f9; color: #374151; border: 1px solid #e5e7eb; border-radius: 8px; padding: 6px 12px; font-size: 11px; font-weight: 700; font-family: 'Nunito', sans-serif; cursor: pointer; transition: background 0.15s; white-space: nowrap; }
.sched-btn:hover { background: #e9eaec; }

.stop-timeline { background: #fff; border-radius: 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); overflow: hidden; }
.stl-row { display: flex; align-items: flex-start; padding: 0 18px; position: relative; cursor: pointer; }
.stl-row:hover .stl-name { color: #1a1c20; }
.stl-track { display: flex; flex-direction: column; align-items: center; width: 24px; flex-shrink: 0; padding-top: 18px; position: relative; }
.stl-track::before { content: ''; position: absolute; top: 0; bottom: 0; left: 50%; transform: translateX(-50%); width: 2px; background: #e8eaed; z-index: 0; }
.stl-row.passed .stl-track::before { background: #d1d5db; }
.stl-row.live .stl-track::before { background: #1db954; }
.stl-row:first-child .stl-track::before { top: 18px; }
.stl-row:last-child .stl-track::before { bottom: calc(100% - 18px); top: 0; }
.stl-dot { width: 16px; height: 16px; border-radius: 50%; border: 2.5px solid #d0d5de; background: #fff; z-index: 1; flex-shrink: 0; transition: all 0.15s; margin-top: 2px; }
.stl-row.passed .stl-dot { border-color: #d1d5db; background: #d1d5db; }
.stl-row.live .stl-dot { border-color: #1db954; background: #1db954; box-shadow: 0 0 0 4px rgba(29,185,84,0.18); width: 20px; height: 20px; margin-top: 0; }
.stl-row.next .stl-dot { border-color: #3b82f6; background: #fff; }
.stl-row.selected .stl-dot { border-color: #2563eb; background: #2563eb; box-shadow: 0 0 0 4px rgba(37,99,235,0.15); }
.stl-content { flex: 1; padding: 14px 0 14px 12px; border-bottom: 1px solid #f4f5f7; }
.stl-row:last-child .stl-content { border-bottom: none; }
.stl-label-row { display: flex; align-items: center; gap: 8px; }
.stl-name { font-size: 13px; font-weight: 600; color: #6b7280; transition: color 0.12s; }
.stl-row.live .stl-name { font-size: 14px; font-weight: 800; color: #1a1c20; }
.stl-row.next .stl-name { font-weight: 700; color: #1a1c20; }
.stl-row.passed .stl-name { color: #b0b7c3; }
.stl-row.selected .stl-name { font-weight: 800; color: #2563eb; }
.stl-badge { font-size: 9px; font-family: 'DM Mono', monospace; font-weight: 600; padding: 2px 7px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.4px; white-space: nowrap; flex-shrink: 0; }
.stl-badge.current { background: #1db954; color: #fff; }
.stl-badge.next { background: #dbeafe; color: #1d4ed8; }
.stl-sub { font-size: 11px; color: #aab0bc; margin-top: 3px; font-family: 'DM Mono', monospace; }

.empty-state { background: #fff; border-radius: 16px; padding: 40px 20px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.055); }
.empty-text { font-size: 13px; font-weight: 700; color: #c8cdd6; margin-bottom: 4px; }
.empty-sub { font-size: 12px; color: #d4d8df; }

.map-panel { flex: 1; min-width: 0; position: sticky; top: 24px; }
.map-card { background: #fff; border-radius: 20px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08); border: 1.5px solid #e8eaed; }
.map-card-header { padding: 16px 20px; border-bottom: 1px solid #f0f2f5; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.map-card-title { font-size: 14px; font-weight: 800; color: #1a1c20; }
.map-card-sub { font-size: 11px; color: #aab0bc; margin-top: 2px; font-family: 'DM Mono', monospace; }
.map-legend { display: flex; gap: 14px; align-items: center; flex-shrink: 0; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: #6b7280; white-space: nowrap; }
.legend-live { width: 10px; height: 10px; border-radius: 50%; background: #1db954; }
.map-placeholder { height: 500px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; background: #fafbfc; }
.map-ph-text { font-size: 15px; font-weight: 700; color: #c8cdd6; }
.map-ph-sub { font-size: 12px; color: #d4d8df; }
.leaflet-container { height: 500px !important; width: 100% !important; }
.leaflet-popup-content-wrapper { border-radius: 12px !important; box-shadow: 0 8px 28px rgba(0,0,0,0.12) !important; border: 1px solid #e8eaed !important; padding: 0 !important; }
.leaflet-popup-content { margin: 0 !important; padding: 12px 16px !important; }
.popup-route { font-size: 10px; font-family: 'DM Mono', monospace; color: #aab0bc; text-transform: uppercase; }
.popup-stop { font-size: 15px; font-weight: 800; color: #1a1c20; margin-top: 3px; }
.popup-tag { display: inline-block; margin-top: 6px; font-size: 10px; font-family: 'DM Mono', monospace; font-weight: 600; padding: 2px 7px; border-radius: 4px; }
.popup-tag-live { background: #e6f7ee; color: #1db954; }
.popup-tag-next { background: #dbeafe; color: #1d4ed8; }
.leaflet-control-zoom { border: 1px solid #e8eaed !important; border-radius: 10px !important; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important; }
.leaflet-control-zoom a { background: #fff !important; color: #1a1c20 !important; border-color: #e8eaed !important; width: 32px !important; height: 32px !important; line-height: 32px !important; }
.leaflet-control-zoom a:hover { background: #f4f6f9 !important; }
.leaflet-control-attribution { font-size: 10px !important; }

.modal-overlay { position: fixed; inset: 0; z-index: 1000; background: rgba(15,17,22,0.5); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; padding: 24px; animation: overlayIn 0.18s ease; }
@keyframes overlayIn { from { opacity:0; } to { opacity:1; } }
.modal { background: #fff; border-radius: 24px; width: 100%; max-width: 820px; max-height: 88vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 24px 80px rgba(0,0,0,0.2); animation: modalIn 0.2s cubic-bezier(0.34,1.4,0.64,1); }
@keyframes modalIn { from { opacity:0; transform:scale(0.95) translateY(12px); } to { opacity:1; transform:scale(1) translateY(0); } }
.modal-head { padding: 24px 24px 0; flex-shrink: 0; }
.modal-head-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 20px; }
.modal-route-info { display: flex; align-items: center; gap: 12px; }
.modal-badge-pill { padding: 6px 16px; border-radius: 20px; font-family: 'DM Mono', monospace; font-size: 13px; font-weight: 600; color: #fff; flex-shrink: 0; }
.modal-route-name { font-size: 20px; font-weight: 900; color: #1a1c20; line-height: 1.2; }
.modal-route-path { font-size: 12px; color: #9ca3af; margin-top: 2px; }
.modal-close { width: 34px; height: 34px; border-radius: 50%; background: #f3f4f6; border: none; font-size: 16px; color: #6b7280; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: background 0.12s; }
.modal-close:hover { background: #e5e7eb; color: #1a1c20; }
.modal-controls { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.day-strip { display: flex; gap: 4px; flex-wrap: nowrap; }
.day-pill { padding: 6px 13px; border-radius: 20px; font-size: 12px; font-weight: 700; cursor: pointer; border: 1.5px solid #e5e7eb; background: #fff; color: #9ca3af; font-family: 'Nunito', sans-serif; white-space: nowrap; transition: all 0.12s; }
.day-pill:hover { border-color: #d1d5db; color: #374151; }
.day-pill.active { color: #fff; border-color: transparent; }
.dir-toggle { display: flex; background: #f3f4f6; border-radius: 10px; padding: 3px; gap: 2px; flex-shrink: 0; }
.dir-btn { padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer; border: none; background: none; color: #9ca3af; font-family: 'Nunito', sans-serif; transition: all 0.12s; white-space: nowrap; display: flex; align-items: center; gap: 5px; }
.dir-btn.active { background: #fff; color: #1a1c20; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.modal-divider { height: 1px; background: #f3f4f6; margin: 16px 0 0; }
.sched-grid-wrap { flex: 1; overflow: auto; scrollbar-width: thin; scrollbar-color: #e5e7eb transparent; }
.sched-grid-wrap::-webkit-scrollbar { width: 4px; height: 4px; }
.sched-grid-wrap::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 2px; }
.sched-table { display: table; width: max-content; min-width: 100%; border-collapse: collapse; }
.sched-thead { display: table-header-group; }
.sched-tr-head { display: table-row; }
.sched-th-stop { display: table-cell; position: sticky; left: 0; z-index: 3; width: 148px; min-width: 148px; padding: 11px 12px 11px 24px; background: #fafafa; font-size: 10px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: #9ca3af; border-right: 1px solid #f0f2f5; border-bottom: 2px solid #f0f2f5; vertical-align: middle; }
.sched-th-trips { display: table-cell; padding: 11px 16px; background: #fff; font-size: 10px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: #9ca3af; border-bottom: 2px solid #f0f2f5; white-space: nowrap; vertical-align: middle; }
.sched-count-pill { display: inline-block; background: #f3f4f6; color: #9ca3af; font-size: 10px; font-family: 'DM Mono', monospace; font-weight: 500; padding: 2px 8px; border-radius: 10px; text-transform: none; letter-spacing: 0; margin-left: 6px; }
.sched-tbody { display: table-row-group; }
.sched-tr { display: table-row; }
.sched-tr:last-child .sched-td-stop, .sched-tr:last-child .sched-td-times { border-bottom: none; }
.sched-td-stop { display: table-cell; position: sticky; left: 0; z-index: 2; width: 148px; min-width: 148px; padding: 14px 12px 14px 24px; vertical-align: middle; background: #fafafa; border-right: 1px solid #f0f2f5; border-bottom: 1px solid #f3f4f6; }
.sched-stop-inner { display: flex; align-items: center; gap: 9px; }
.sched-stop-dot { width: 9px; height: 9px; border-radius: 50%; border: 2px solid; background: #fff; flex-shrink: 0; }
.sched-stop-name { font-size: 12px; font-weight: 700; color: #1a1c20; white-space: nowrap; }
.sched-td-times { display: table-cell; padding: 14px 16px; vertical-align: middle; border-bottom: 1px solid #f3f4f6; }
.sched-times-inner { display: flex; align-items: center; gap: 5px; }
.sched-time-pill { font-family: 'DM Mono', monospace; font-size: 11px; font-weight: 500; color: #374151; background: #f8f9fb; border-radius: 7px; padding: 5px 8px; border: 1px solid #eef0f3; white-space: nowrap; flex-shrink: 0; transition: background 0.1s, border-color 0.1s, color 0.1s; cursor: default; }
.sched-time-pill:hover { background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; }
.no-service-msg { padding: 52px; text-align: center; color: #d1d5db; font-size: 13px; font-weight: 600; }
`;

function ScheduleModal({ route, onClose }) {
  const today = new Date().getDay();
  const dayLabels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
  const initDay = today === 0 ? 6 : today - 1;
  const [selectedDay, setSelectedDay] = useState(dayLabels[initDay] || "Mon");
  const [direction, setDirection] = useState("up");

  const dayKey = getDayKey(selectedDay);
  const baseTimes = route.timetable[dayKey] || [];

  const stops   = direction === "up" ? [...route.stops]       : [...route.stops].reverse();
  const offsets = direction === "up" ? [...route.stopOffsets] : [...route.stopOffsets].map(o => route.stopOffsets[route.stopOffsets.length - 1] - o).reverse();

  useEffect(() => {
    const fn = e => e.key === "Escape" && onClose();
    window.addEventListener("keydown", fn);
    return () => window.removeEventListener("keydown", fn);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-head">
          <div className="modal-head-top">
            <div className="modal-route-info">
              <div className="modal-badge-pill" style={{ background: route.color }}>{route.id}</div>
              <div>
                <div className="modal-route-name">{route.name}</div>
                <div className="modal-route-path">
                  {direction === "up" ? `${route.from} → ${route.to}` : `${route.to} → ${route.from}`}
                </div>
              </div>
            </div>
            <button className="modal-close" onClick={onClose}>✕</button>
          </div>
          <div className="modal-controls">
            <div className="day-strip">
              {dayLabels.map(d => (
                <button key={d} className={`day-pill ${selectedDay === d ? "active" : ""}`}
                  style={selectedDay === d ? { background: route.color } : {}}
                  onClick={() => setSelectedDay(d)}>{d}</button>
              ))}
            </div>
            <div className="dir-toggle">
              <button className={`dir-btn ${direction === "up" ? "active" : ""}`} onClick={() => setDirection("up")}>↑ Up</button>
              <button className={`dir-btn ${direction === "down" ? "active" : ""}`} onClick={() => setDirection("down")}>↓ Down</button>
            </div>
          </div>
          <div className="modal-divider" />
        </div>
        <div className="sched-grid-wrap">
          {baseTimes.length === 0 ? (
            <div className="no-service-msg">No service on {selectedDay}</div>
          ) : (
            <div className="sched-table">
              <div className="sched-thead">
                <div className="sched-tr-head">
                  <div className="sched-th-stop">Stop</div>
                  <div className="sched-th-trips">Trips<span className="sched-count-pill">{baseTimes.length} departures</span></div>
                </div>
              </div>
              <div className="sched-tbody">
                {stops.map((stop, si) => {
                  const times = baseTimes.map(t => addMinutes(t, offsets[si]));
                  const isFirst = si === 0;
                  const isLast = si === stops.length - 1;
                  return (
                    <div key={stop} className="sched-tr">
                      <div className="sched-td-stop">
                        <div className="sched-stop-inner">
                          <div className="sched-stop-dot" style={{ borderColor: route.color, background: isFirst || isLast ? route.color : "#fff" }} />
                          <span className="sched-stop-name">{stop}</span>
                        </div>
                      </div>
                      <div className="sched-td-times">
                        <div className="sched-times-inner">
                          {times.map((t, ti) => <span key={ti} className="sched-time-pill">{t}</span>)}
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

function StopTimeline({ route, searchedStop, selectedStop, onStopClick, onScheduleClick }) {
  const liveIdx = route.stops.indexOf(route.liveStop);
  return (
    <div>
      <div className="route-header-card">
        <div className="rhc-top">
          <div className="rhc-badge">{route.id}</div>
          <div className="rhc-info">
            <div className="rhc-name">{route.name}</div>
            <div className="rhc-path">{route.from} → {route.to}</div>
          </div>
        </div>
        <div className="rhc-meta">
          <span className="rhc-tag">{route.stops.length} stops</span>
          <button className="sched-btn" onClick={onScheduleClick}>View Schedule →</button>
        </div>
      </div>
      <div className="stop-timeline">
        {route.stops.map((stop, i) => {
          const isLive     = i === liveIdx;
          const isNext     = i === liveIdx + 1;
          const isPassed   = i < liveIdx;
          const isSelected = stop === selectedStop;
          const isSearched = stop === searchedStop;
          const eta        = isNext ? (route.etaFromLive?.[stop] ?? null) : null;
          let cls = "stl-row";
          if (isSelected || isSearched) cls += " selected";
          else if (isLive)   cls += " live";
          else if (isNext)   cls += " next";
          else if (isPassed) cls += " passed";
          return (
            <div key={stop} className={cls} onClick={() => onStopClick(stop)}>
              <div className="stl-track"><div className="stl-dot" /></div>
              <div className="stl-content">
                <div className="stl-label-row">
                  <span className="stl-name">{stop}</span>
                  {isLive && <span className="stl-badge current">Current Stop</span>}
                  {isNext && !isLive && <span className="stl-badge next">Next Stop</span>}
                </div>
                {isLive && <div className="stl-sub">Bus is here now</div>}
                {isNext && eta !== null && <div className="stl-sub">ETA ~{eta} min</div>}
                {isPassed && <div className="stl-sub">Already passed</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function CustomerPage() {
  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);
  const [activeRoute, setActiveRoute] = useState(null);
  const [selectedStop, setSelectedStop] = useState(null);
  const [activeTabRouteId, setActiveTabRouteId] = useState(null);
  const [scheduleRoute, setScheduleRoute] = useState(null);
  const inputRef = useRef(null);
  const q = query.toLowerCase().trim();

  const filtered = q
    ? SUGGESTIONS.filter(s =>
        s.label.toLowerCase().includes(q) ||
        (s.type === "route" && s.data?.stops?.some(st => st.toLowerCase().includes(q)))
      ).slice(0, 12)
    : SUGGESTIONS.slice(0, 10);

  const routeSuggs = filtered.filter(s => s.type === "route");
  const stopSuggs  = filtered.filter(s => s.type === "stop");

  const searchedStopName = (() => {
    if (!q) return null;
    return ALL_STOPS.find(s => s.toLowerCase() === q || s.toLowerCase().includes(q)) || null;
  })();

  const routesForStop = searchedStopName && !activeRoute
    ? ROUTES.filter(r => r.stops.includes(searchedStopName))
    : [];

  const timelineRoute = (() => {
    if (activeRoute) return ROUTES.find(r => r.id === activeRoute) || null;
    if (routesForStop.length > 0) {
      const tabId = activeTabRouteId || routesForStop[0].id;
      return ROUTES.find(r => r.id === tabId) || routesForStop[0];
    }
    return null;
  })();

  const mapRouteData = timelineRoute;
  const showTimeline  = !!timelineRoute;
  const showRouteTabs = routesForStop.length > 1 && !activeRoute;

  const displayRoutes = q
    ? ROUTES.filter(r =>
        r.id.toLowerCase().includes(q) ||
        r.name.toLowerCase().includes(q) ||
        r.from.toLowerCase().includes(q) ||
        r.to.toLowerCase().includes(q) ||
        r.stops.some(s => s.toLowerCase().includes(q))
      )
    : ROUTES;

  const handleSelect = (sug) => {
    setFocused(false);
    setSelectedStop(null);
    if (sug.type === "route") {
      setQuery(`Route ${sug.id} – ${sug.data.from} to ${sug.data.to}`);
      setActiveRoute(sug.id);
      setActiveTabRouteId(sug.id);
    } else {
      setQuery(sug.label);
      setActiveRoute(null);
      const r = ROUTES.filter(r => r.stops.includes(sug.label));
      setActiveTabRouteId(r[0]?.id || null);
    }
  };

  const handleChip = (chip) => {
    setQuery(chip); setActiveRoute(null); setSelectedStop(null); setActiveTabRouteId(null);
    inputRef.current?.focus();
  };

  const handleFind = () => {
    setFocused(false);
    if (displayRoutes.length === 1) { setActiveRoute(displayRoutes[0].id); setActiveTabRouteId(displayRoutes[0].id); }
  };

  const handleStopClick = (stopName) => setSelectedStop(prev => prev === stopName ? null : stopName);

  const handleCardClick = (routeId) => {
    setActiveRoute(prev => { const next = prev === routeId ? null : routeId; setActiveTabRouteId(next); return next; });
    setSelectedStop(null);
  };

  const clearSearch = () => { setQuery(""); setActiveRoute(null); setSelectedStop(null); setActiveTabRouteId(null); };

  return (
    <>
      <style>{CSS}</style>

      {scheduleRoute && <ScheduleModal route={scheduleRoute} onClose={() => setScheduleRoute(null)} />}

      <div className="hero">
        <h1 className="hero-title">Find your <span className="highlight">route</span>,<br />reach on time.</h1>
        <p className="hero-sub">Search any bus number, route name, or stop across Delhi</p>
        <div className="search-outer">
          <div className="search-bar">
            <input
              ref={inputRef} className="search-input"
              placeholder="Search route number / stop name…"
              value={query}
              onChange={e => { setQuery(e.target.value); setActiveRoute(null); setSelectedStop(null); setActiveTabRouteId(null); }}
              onFocus={() => setFocused(true)}
              onBlur={() => setTimeout(() => setFocused(false), 180)}
              onKeyDown={e => e.key === "Enter" && handleFind()}
            />
            {query && (
              <button style={{ background:"none", border:"none", cursor:"pointer", color:"#aab0bc", fontSize:18, padding:"0 8px" }} onClick={clearSearch}>×</button>
            )}
            <button className="find-btn" onClick={handleFind}>Find Route →</button>
          </div>
          {focused && (
            <div className="dropdown">
              {filtered.length === 0 && <div className="dd-no-result">No results for "{query}"</div>}
              {routeSuggs.length > 0 && (
                <div className="dd-section">
                  <div className="dd-section-label">Routes</div>
                  {routeSuggs.map(s => (
                    <div key={s.id} className="dd-item" onMouseDown={() => handleSelect(s)}>
                      <div className="dd-text-main">{s.label}</div>
                    </div>
                  ))}
                </div>
              )}
              {stopSuggs.length > 0 && (
                <div className="dd-section">
                  <div className="dd-section-label">Stops</div>
                  {stopSuggs.map(s => (
                    <div key={s.id} className="dd-item" onMouseDown={() => handleSelect(s)}>
                      <div className="dd-text-main">{s.label}</div>
                      <div className="dd-text-sub">{s.sub}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
        <div className="chips-row">
          {QUICK_CHIPS.map(c => <div key={c} className="chip" onClick={() => handleChip(c)}>{c}</div>)}
        </div>
      </div>

      <div className="body-layout">
        <div className="left-panel">
          {showTimeline ? (
            <>
              <div className="panel-heading">
                {searchedStopName && !activeRoute ? `Routes via ${searchedStopName}` : "Route Details"}
              </div>
              {showRouteTabs && (
                <div className="route-tabs">
                  {routesForStop.map(r => (
                    <button key={r.id} className={`rtab ${(activeTabRouteId || routesForStop[0].id) === r.id ? "active" : ""}`}
                      onClick={() => setActiveTabRouteId(r.id)}>{r.id}</button>
                  ))}
                </div>
              )}
              <StopTimeline
                route={timelineRoute}
                searchedStop={searchedStopName}
                selectedStop={selectedStop}
                onStopClick={handleStopClick}
                onScheduleClick={() => setScheduleRoute(timelineRoute)}
              />
            </>
          ) : (
            <>
              <div className="panel-heading">
                {q ? `Results for "${query}"` : "All Routes"} — {displayRoutes.length} found
              </div>
              {displayRoutes.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-text">No routes found</div>
                  <div className="empty-sub">Try a stop name or route number</div>
                </div>
              ) : displayRoutes.map(r => (
                <div key={r.id}
                  style={{ background:"#fff", borderRadius:14, padding:"14px 16px", marginBottom:8, display:"flex", alignItems:"center", gap:14, boxShadow:"0 1px 4px rgba(0,0,0,0.07)", cursor:"pointer", border:`1.5px solid ${activeRoute === r.id ? "#d1d5db" : "#f0f2f5"}` }}
                  onClick={() => handleCardClick(r.id)}
                >
                  <div style={{ width:42, height:42, borderRadius:10, background:"#f4f6f9", display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}>
                    <span style={{ fontFamily:"'DM Mono',monospace", fontSize:12, fontWeight:600, color:"#6b7280" }}>{r.id}</span>
                  </div>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ fontSize:13, fontWeight:700, color:"#1a1c20" }}>{r.name}</div>
                    <div style={{ fontSize:11, color:"#9ca3af", marginTop:2, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{r.from} → {r.to}</div>
                  </div>
                  <div style={{ textAlign:"right", flexShrink:0 }}>
                    <button
                      style={{ background:"#f4f6f9", color:"#374151", border:"1px solid #e5e7eb", borderRadius:6, padding:"4px 10px", fontSize:10, fontWeight:700, fontFamily:"'Nunito',sans-serif", cursor:"pointer" }}
                      onClick={e => { e.stopPropagation(); setScheduleRoute(r); }}
                    >Schedule</button>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>

        <div className="map-panel">
          <div className="map-card">
            <div className="map-card-header">
              <div>
                <div className="map-card-title">
                  {mapRouteData ? `Route ${mapRouteData.id} – ${mapRouteData.name}` : "Route Viewer"}
                </div>
                <div className="map-card-sub">
                  {mapRouteData ? `${mapRouteData.from} → ${mapRouteData.to} · ${mapRouteData.stops.length} stops` : "Click any route to view it on the map"}
                </div>
              </div>
              <div className="map-legend">
                <div className="legend-item"><div className="legend-live" />Live bus</div>
              </div>
            </div>

            {mapRouteData ? (
              <MapContainer center={[28.6139, 77.209]} zoom={12} style={{ height:"500px", width:"100%" }}>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
                  url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                />
                <FitBounds coords={mapRouteData.coords} />
                <Polyline positions={mapRouteData.coords} pathOptions={{ color: mapRouteData.color, weight: 5, opacity: 0.85 }} />
                {mapRouteData.coords.map((pos, i) => {
                  const stopName   = mapRouteData.stops[i];
                  const liveIdx    = mapRouteData.stops.indexOf(mapRouteData.liveStop);
                  const isLive     = i === liveIdx;
                  const isNext     = i === liveIdx + 1;
                  const isSelected = stopName === selectedStop;
                  const isSearched = stopName === searchedStopName;
                  const stroke = isNext ? "#3b82f6" : isSelected || isSearched ? "#1d4ed8" : isLive ? "#1db954" : mapRouteData.color;
                  const fill   = isNext ? "#fff" : isSelected || isSearched ? "#60a5fa" : isLive ? "#1db954" : "#fff";
                  const radius = isLive ? 10 : isNext ? 9 : isSelected || isSearched ? 11 : 7;
                  const eta    = isNext ? (mapRouteData.etaFromLive?.[stopName] ?? null) : null;
                  return (
                    <CircleMarker key={i} center={pos} radius={radius}
                      pathOptions={{ color: stroke, fillColor: fill, fillOpacity: 1, weight: 2.5 }}
                      eventHandlers={{ click: () => handleStopClick(stopName) }}
                    >
                      <Popup>
                        <div className="popup-route">Route {mapRouteData.id} · {mapRouteData.name}</div>
                        <div className="popup-stop">{stopName}</div>
                        {isLive && <div><span className="popup-tag popup-tag-live">Current Stop</span></div>}
                        {isNext && <div><span className="popup-tag popup-tag-next">Next Stop{eta ? ` · ETA ~${eta} min` : ""}</span></div>}
                      </Popup>
                    </CircleMarker>
                  );
                })}
              </MapContainer>
            ) : (
              <div className="map-placeholder">
                <div className="map-ph-text">No route selected</div>
                <div className="map-ph-sub">Pick a route from the list to see it here</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}