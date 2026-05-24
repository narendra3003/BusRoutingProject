import React, { useEffect, useState } from "react";

function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  // -------------------------
  // FETCH DASHBOARD DATA
  // -------------------------
  const fetchDashboard = async () => {
    try {
      setLoading(true);

      const res = await fetch(
        "http://localhost:8000/analytics/dashboard",
        {
          headers: {
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
        }
      );

      if (!res.ok) throw new Error("Failed to load dashboard");

      const result = await res.json();
      setData(result);

      /*
      RESPONSE:
      {
        total_trips_today: 42,
        active_drivers: 18,
        active_buses: 12,
        delayed_trips: 5,
        recent_overrides: [...]
      }
      */

    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  // -------------------------
  // UI
  // -------------------------
  return (
    <div className="p-6 space-y-6">

      <h1 className="text-2xl font-bold">
      
        Admin Dashboard</h1>


      {loading && <p>Loading...</p>}

      {data && (
        <>
              {/* Quick Links Section */}
      <div className="bg-white rounded-xl shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">
          Data Feeds
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

          {/* Stops */}
          <a
            href="/stops-data-feed"
            className="group bg-[#E6F1FB] rounded-2xl p-6 shadow-sm hover:shadow-lg transition duration-300 border border-gray-100"
          >
            <div className="flex items-center gap-4">
              {/* <div className="p-3 bg-purple-100 text-purple-600 rounded-xl group-hover:scale-110 transition">
                <Map size={24} />
              </div> */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  Stops Data
                </h3>
                <p className="text-gray-500 text-sm">
                  Manage stop locations and details
                </p>
              </div>
            </div>
          </a>

          {/* Routes */}
          <a
            href="/routes-data-feed"
            className="group bg-[#E6F1FB] rounded-2xl p-6 shadow-sm hover:shadow-lg transition duration-300 border border-gray-100"
          >
            <div className="flex items-center gap-4">
              {/* <div className="p-3 bg-blue-100 text-blue-600 rounded-xl group-hover:scale-110 transition">
                <Database size={24} />
              </div> */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  Routes Data
                </h3>
                <p className="text-gray-500 text-sm">
                  Configure routes and paths
                </p>
              </div>
            </div>
          </a>


          {/* Route Builder */}
          <a
            href="/route-builder"
            className="group bg-[#E6F1FB] rounded-2xl p-6 shadow-sm hover:shadow-lg transition duration-300 border border-gray-100"
          >
            <div className="flex items-center gap-4">
              {/* <div className="p-3 bg-orange-100 text-orange-600 rounded-xl group-hover:scale-110 transition">
                <Route size={24} />
              </div> */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  Route Builder
                </h3>
                <p className="text-gray-500 text-sm">
                  Design and visualize bus routes
                </p>
              </div>
            </div>
          </a>

          {/* Buses */}
          <a
            href="/buses-data-feed"
            className="group bg-[#E6F1FB] rounded-2xl p-6 shadow-sm hover:shadow-lg transition duration-300 border border-gray-100"
          >
            <div className="flex items-center gap-4">
              {/* <div className="p-3 bg-green-100 text-green-600 rounded-xl group-hover:scale-110 transition">
                <Bus size={24} />
              </div> */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  Buses Data
                </h3>
                <p className="text-gray-500 text-sm">
                  Monitor and manage bus fleet
                </p>
              </div>
            </div>
          </a>

          {/* Drivers */}
          <a
            href="/driver-data-feed"
            className="group bg-[#E6F1FB] rounded-2xl p-6 shadow-sm hover:shadow-lg transition duration-300 border border-gray-100"
          >
            <div className="flex items-center gap-4">
              {/* <div className="p-3 bg-yellow-100 text-yellow-600 rounded-xl group-hover:scale-110 transition">
                <User size={24} />
              </div> */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  Drivers Data
                </h3>
                <p className="text-gray-500 text-sm">
                  Manage driver information and schedules
                </p>
              </div>
            </div>
          </a>

          <a
            href="/schedule"
            className="group bg-[#E6F1FB] rounded-2xl p-6 shadow-sm hover:shadow-lg transition duration-300 border border-gray-100"
          >
            <div className="flex items-center gap-4">
              {/* <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl group-hover:scale-110 transition">
                <Clock size={24} />
              </div> */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  Schedule Management
                </h3>
                <p className="text-gray-500 text-sm">
                  View and manage bus schedules
                </p>
              </div>
            </div>
          </a>

          <a
            href="/leave-approvals"
            className="group bg-[#E6F1FB] rounded-2xl p-6 shadow-sm hover:shadow-lg transition duration-300 border border-gray-100"
          >
            <div className="flex items-center gap-4">
              {/* <div className="p-3 bg-purple-100 text-purple-600 rounded-xl group-hover:scale-110 transition">
                <Calendar size={24} />
              </div> */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  Leave Approvals
                </h3>
                <p className="text-gray-500 text-sm">
                  Review and approve driver leave requests
                </p>
              </div>
            </div>
          </a>

          <a
            href="/dispatch"
            className="group bg-[#E6F1FB] rounded-2xl p-6 shadow-sm hover:shadow-lg transition duration-300 border border-gray-100"
          >
            <div className="flex items-center gap-4">
              {/* <div className="p-3 bg-red-100 text-red-600 rounded-xl group-hover:scale-110 transition">
                <AlertCircle size={24} />
              </div> */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  Dispatch Center
                </h3>
                <p className="text-gray-500 text-sm">
                  Manage and monitor dispatch operations
                </p>
              </div>
            </div>
          </a>

          <a href="/override" className="group bg-[#E6F1FB] rounded-2xl p-6 shadow-sm hover:shadow-lg transition duration-300 border border-gray-100">
            <div className="flex items-center gap-4">
              {/* <div className="p-3 bg-teal-100 text-teal-600 rounded-xl group-hover:scale-110 transition">
                <AlertTriangle size={24} />
              </div> */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  Override Requests
                </h3>
                <p className="text-gray-500 text-sm">
                  Review and manage override requests
                </p>
              </div>
            </div>
          </a>
        </div>
      </div>
          {/* CARDS */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

            <div className="bg-[#E6F1FB] p-4 shadow rounded text-center">
              <p className="text-gray-500">Total Trips Today</p>
              <p className="text-2xl font-bold">
                {data.total_trips_today}
              </p>
            </div>

            <div className="bg-[#E6F1FB] p-4 shadow rounded text-center">
              <p className="text-gray-500">Active Drivers</p>
              <p className="text-2xl font-bold">
                {data.active_drivers}
              </p>
            </div>

            <div className="bg-[#E6F1FB] p-4 shadow rounded text-center">
              <p className="text-gray-500">Active Buses</p>
              <p className="text-2xl font-bold">
                {data.active_buses}
              </p>
            </div>

            <div className="bg-[#E6F1FB] p-4 shadow rounded text-center">
              <p className="text-gray-500">Delayed Trips</p>
              <p className="text-2xl font-bold text-red-600">
                {data.delayed_trips}
              </p>
            </div>

          </div>

          {/* RECENT OVERRIDES */}
          <div className="bg-[#E6F1FB] p-6 shadow rounded">
            <h2 className="font-semibold mb-4">
              Recent Overrides
            </h2>

            <table className="w-full border text-center">
              <thead className="bg-gray-100">
                <tr>
                  <th>Trip ID</th>
                  <th>Old Driver</th>
                  <th>New Driver</th>
                  <th>Time</th>
                </tr>
              </thead>

              <tbody>
                {data.recent_overrides &&
                  data.recent_overrides.map((o) => (
                    <tr key={o.id} className="border-t">
                      <td>{o.trip_id}</td>
                      <td>{o.old_driver || "-"}</td>
                      <td>{o.new_driver || "-"}</td>
                      <td>
                        {new Date(o.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {message && (
        <p className="text-red-600">{message}</p>
      )}
    </div>
  );
}

export default AdminDashboard;