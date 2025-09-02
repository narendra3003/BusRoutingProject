import React, { useEffect, useState } from "react";
import API from "../api/api";

function AdminDashboard() {
  const [kpi, setKpi] = useState({});
  const [trips, setTrips] = useState([]);
  const [override, setOverride] = useState({ trip_id: "", delta_minutes: "", reason: "" });
  const [upload, setUpload] = useState({ bus_no: "", route_id: "", stop_id: "", boarding_count: "", alighting_count: "" });

  useEffect(() => {
    API.get("/admin/kpis").then(res => setKpi(res.data)).catch(console.log);
    API.get("/admin/schedules").then(res => setTrips(res.data.trips)).catch(console.log);
  }, []);

  const handleOverride = () => {
    API.post("/schedules/override", override)
      .then(() => alert("Override applied")).catch(console.log);
  }

  const handleUpload = () => {
    API.post("/observations/upload", upload)
      .then(() => alert("Observation uploaded")).catch(console.log);
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Admin Dashboard</h2>

      {/* KPI Section */}
      <div className="mb-4 p-2 border rounded">
        <h3 className="font-bold">KPIs</h3>
        <p>Buses Used: {kpi.buses_used}</p>
        <p>Avg Wait Time: {kpi.avg_wait_time}</p>
        <p>Load Factor: {kpi.load_factor}</p>
      </div>

      {/* Trips Table */}
      <div className="mb-4">
        <h3 className="font-bold">Trips</h3>
        <table className="border w-full">
          <thead>
            <tr>
              <th>Trip ID</th><th>Start</th><th>End</th>
            </tr>
          </thead>
          <tbody>
            {trips.map(t => (
              <tr key={t.trip_id}>
                <td>{t.trip_id}</td><td>{t.start_time}</td><td>{t.end_time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Override Form */}
      <div className="mb-4 p-2 border rounded">
        <h3 className="font-bold">Apply Override</h3>
        <input placeholder="Trip ID" onChange={e => setOverride({...override, trip_id: e.target.value})} className="border p-1 m-1"/>
        <input placeholder="Delta Minutes" onChange={e => setOverride({...override, delta_minutes: e.target.value})} className="border p-1 m-1"/>
        <input placeholder="Reason" onChange={e => setOverride({...override, reason: e.target.value})} className="border p-1 m-1"/>
        <button onClick={handleOverride} className="bg-purple-500 text-white px-2 py-1 rounded">Submit</button>
      </div>

      {/* Upload Form */}
      <div className="p-2 border rounded">
        <h3 className="font-bold">Upload Observation</h3>
        <input placeholder="Bus No" onChange={e => setUpload({...upload, bus_no: e.target.value})} className="border p-1 m-1"/>
        <input placeholder="Route ID" onChange={e => setUpload({...upload, route_id: e.target.value})} className="border p-1 m-1"/>
        <input placeholder="Stop ID" onChange={e => setUpload({...upload, stop_id: e.target.value})} className="border p-1 m-1"/>
        <input placeholder="Boarding Count" onChange={e => setUpload({...upload, boarding_count: e.target.value})} className="border p-1 m-1"/>
        <input placeholder="Alighting Count" onChange={e => setUpload({...upload, alighting_count: e.target.value})} className="border p-1 m-1"/>
        <button onClick={handleUpload} className="bg-purple-500 text-white px-2 py-1 rounded">Upload</button>
      </div>
    </div>
  );
}

export default AdminDashboard;
