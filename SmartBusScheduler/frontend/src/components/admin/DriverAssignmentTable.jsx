import React from "react";

function DriverAssignmentTable({ assignments }) {
  if (!assignments.length) return null;

  return (
    <div className="bg-white p-4 shadow rounded">
      <h2 className="text-xl font-bold mb-3">Driver-Route Assignments</h2>
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-blue-100 text-left">
            <th className="p-2 border">Driver ID</th>
            <th className="p-2 border">Trip ID</th>
            {/* <th className="p-2 border">Bus ID</th>
            <th className="p-2 border">Planned Start</th>
            <th className="p-2 border">Planned End</th> */}
          </tr>
        </thead>
        <tbody>
          {assignments.map((a, idx) => (
            <tr key={idx} className="hover:bg-blue-50">
              <td className="p-2 border">{a.assigned_driver_id}</td>
              <td className="p-2 border">{a.trip_id}</td>
              {/* <td className="p-2 border">{a.bus_id}</td>
              <td className="p-2 border">{new Date(a.planned_start).toLocaleString()}</td>
              <td className="p-2 border">{new Date(a.planned_end).toLocaleString()}</td> */}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DriverAssignmentTable;