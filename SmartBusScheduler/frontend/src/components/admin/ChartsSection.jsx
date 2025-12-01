import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts";

const COLORS = ["#4CAF50", "#2196F3", "#FFC107", "#9C27B0", "#FF5722"];

function ChartsSection({ schedule }) {
  if (!schedule.length) return null;

  // Count trips per route
  const routeData = Object.values(
    schedule.reduce((acc, trip) => {
      const route = trip.route_id || "Unknown";
      acc[route] = acc[route] || { route, trips: 0 };
      acc[route].trips += 1;
      return acc;
    }, {})
  );

  // Count trips per driver
  const driverData = Object.values(
    schedule.reduce((acc, trip) => {
      const driver = trip.assigned_driver_id || "Unassigned";
      acc[driver] = acc[driver] || { driver, trips: 0 };
      acc[driver].trips += 1;
      return acc;
    }, {})
  );

  return (
    <div className="bg-white p-6 rounded shadow grid grid-cols-1">
      {/* Pie Chart for Routes */}
      <div>
        <h3 className="text-lg font-bold mb-3 text-center">Trips per Route</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={routeData}
              dataKey="trips"
              nameKey="route"
              cx="50%"
              cy="50%"
              outerRadius={100}
              fill="#8884d8"
              label
            >
              {routeData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Bar Chart for Drivers */}
      <div>
        <h3 className="text-lg font-bold mb-3 text-center">Trips per Driver</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={driverData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="driver" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="trips" fill="#2196F3" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default ChartsSection;