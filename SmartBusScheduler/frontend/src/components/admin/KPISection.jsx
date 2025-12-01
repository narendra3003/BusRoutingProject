import React from "react";

function KPISection({ schedule, driverAssignments }) {
  const totalDrivers = driverAssignments.length;
  const totalRoutes = new Set(schedule.map(s => s.route_id)).size;
  const totalTrips = schedule.length;
  const avgTripsPerDriver = totalDrivers
    ? (totalTrips / totalDrivers).toFixed(1)
    : 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-4">
      <div className="bg-green-100 p-4 rounded shadow">
        <h3 className="font-bold text-lg">Total Drivers</h3>
        <p>{totalDrivers}</p>
      </div>
      <div className="bg-blue-100 p-4 rounded shadow">
        <h3 className="font-bold text-lg">Total Routes</h3>
        <p>{totalRoutes}</p>
      </div>
      <div className="bg-yellow-100 p-4 rounded shadow">
        <h3 className="font-bold text-lg">Total Trips</h3>
        <p>{totalTrips}</p>
      </div>
      <div className="bg-purple-100 p-4 rounded shadow">
        <h3 className="font-bold text-lg">Avg Trips / Driver</h3>
        <p>{avgTripsPerDriver}</p>
      </div>
    </div>
  );
}

export default KPISection;