import React, { useEffect, useState } from "react";
import API from "../api/api";

function CustomerDashboard() {
  const [routes, setRoutes] = useState([]);
  const [stops, setStops] = useState([]);
  const [selectedRoute, setSelectedRoute] = useState("");
  const [selectedStop, setSelectedStop] = useState("");
  const [schedule, setSchedule] = useState({ previous_trips: [], next_trips: [] });

  useEffect(() => {
    API.get("/routes").then(res => setRoutes(res.data)).catch(console.log);
  }, []);

  const fetchStops = (routeId) => {
    setSelectedRoute(routeId);
    API.get(`/routes/${routeId}/stops`).then(res => setStops(res.data.stops)).catch(console.log);
  }

  const fetchSchedule = () => {
    if (!selectedRoute || !selectedStop) return;
    API.get(`/schedules/${selectedRoute}?stop_id=${selectedStop}`)
      .then(res => setSchedule(res.data))
      .catch(console.log);
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Customer Dashboard</h2>

      <div className="flex space-x-4 mb-4">
        <select value={selectedRoute} onChange={e => fetchStops(e.target.value)} className="border p-2">
          <option value="">Select Route</option>
          {routes.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
        </select>

        <select value={selectedStop} onChange={e => setSelectedStop(e.target.value)} className="border p-2">
          <option value="">Select Stop</option>
          {stops.map(s => <option key={s.stop_id} value={s.stop_id}>{s.stop_name}</option>)}
        </select>

        <button onClick={fetchSchedule} className="bg-purple-500 text-white px-4 py-2 rounded">View Schedule</button>
      </div>

      <div className="mb-4">
        <h3 className="font-bold">Previous Trips</h3>
        <ul>
          {schedule.previous_trips.map(t => <li key={t.trip_id}>{t.arrival_time} → {t.departure_time} ({t.stop_name})</li>)}
        </ul>
      </div>

      <div>
        <h3 className="font-bold">Next Trips</h3>
        <ul>
          {schedule.next_trips.map(t => <li key={t.trip_id}>{t.arrival_time} → {t.departure_time} ({t.stop_name})</li>)}
        </ul>
      </div>
    </div>
  );
}

export default CustomerDashboard;
