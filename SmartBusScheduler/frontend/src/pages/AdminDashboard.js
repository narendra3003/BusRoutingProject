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
return (
  <div className="min-h-screen bg-gray-100">

    {/* NAVBAR */}
    <div className="bg-white shadow px-6 py-4 flex justify-between items-center sticky top-0 z-10">
      <h1 className="text-xl font-bold">Admin Dashboard</h1>
    </div>

    <div className="p-6 space-y-8">

      {loading && <p>Loading...</p>}

      {data && (
        <>
          {/* DATA MANAGEMENT */}
          <div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { name: "Stops", link: "/stops-data-feed" },
                { name: "Routes", link: "/routes-data-feed" },
                { name: "Route Builder", link: "/route-builder" },
                { name: "Buses", link: "/buses-data-feed" },
                { name: "Drivers", link: "/driver-data-feed" },
                { name: "Schedule", link: "/schedule" },
                { name: "Leave Approvals", link: "/leave-approvals" },
                { name: "Overrides", link: "/override" },
              ].map((item) => (
                <a
                  key={item.name}
                  href={item.link}
                  className="bg-white p-4 rounded shadow hover:shadow-md hover:bg-purple-50 transition text-center font-medium"
                >
                  {item.name}
                </a>
              ))}
            </div>
          </div>

          {/* STATS CARDS */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card title="Total Trips Today" value={data.total_trips_today} />
            <Card title="Active Drivers" value={data.active_drivers} />
            <Card title="Active Buses" value={data.active_buses} />
            <Card
              title="Delayed Trips"
              value={data.delayed_trips}
              highlight
            />
          </div>

          {/* RECENT OVERRIDES */}
          <div className="bg-white p-6 shadow rounded overflow-x-auto">
            <h2 className="font-semibold mb-4">Recent Overrides</h2>

            <table className="w-full text-sm">
              <thead className="bg-gray-100 text-gray-600">
                <tr>
                  <th className="p-2">Trip ID</th>
                  <th className="p-2">Old Driver</th>
                  <th className="p-2">New Driver</th>
                  <th className="p-2">Time</th>
                </tr>
              </thead>

              <tbody>
                {data.recent_overrides?.map((o) => (
                  <tr key={o.id} className="border-t text-center">
                    <td className="p-2">{o.trip_id}</td>
                    <td className="p-2">{o.old_driver || "-"}</td>
                    <td className="p-2">{o.new_driver || "-"}</td>
                    <td className="p-2">
                      {new Date(o.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {message && <p className="text-red-600">{message}</p>}
    </div>
  </div>
)};


export default AdminDashboard;

const Card = ({ title, value, highlight }) => (
  <div className="bg-white p-4 shadow rounded text-center">
    <p className="text-gray-500 text-sm">{title}</p>
    <p
      className={`text-2xl font-bold ${
        highlight ? "text-red-600" : "text-gray-800"
      }`}
    >
      {value}
    </p>
  </div>
);