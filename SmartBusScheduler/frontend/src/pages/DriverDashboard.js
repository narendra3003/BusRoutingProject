import React, { useEffect, useState } from "react";
import API from "../api/api";

function DriverDashboard() {
  const [trips, setTrips] = useState([]);
  const driverId = sessionStorage.getItem("driver_id") || 1; // Replace with real ID from login

  useEffect(() => {
    API.get(`/drivers/${driverId}/trips`).then(res => setTrips(res.data.assigned_trips)).catch(console.log);
  }, [driverId]);

  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Driver Dashboard</h2>
      <table className="border w-full">
        <thead>
          <tr>
            <th>Trip ID</th><th>Report Time</th><th>Route ID</th>
          </tr>
        </thead>
        <tbody>
          {trips.map(t => (
            <tr key={t.trip_id}>
              <td>{t.trip_id}</td><td>{t.report_time}</td><td>{t.route_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DriverDashboard;
