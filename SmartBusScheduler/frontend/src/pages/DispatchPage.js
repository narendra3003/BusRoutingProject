import React, { useEffect, useState } from "react";

function DispatchPage() {
  const [trips, setTrips] = useState([]);
  const [routes, setRoutes] = useState([]);

  const [filters, setFilters] = useState({
    date: "",
    route_id: "",
    status: "",
  });

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // -------------------------
  // FETCH ROUTES
  // -------------------------
  const fetchRoutes = async () => {
    try {
      const res = await fetch("http://localhost:8000/routes");
      const data = await res.json();
      setRoutes(data);
    } catch {
      setMessage("Failed to load routes");
    }
  };

  useEffect(() => {
    fetchRoutes();
  }, []);

  // -------------------------
  // FETCH DISPATCH DATA
  // -------------------------
  const fetchDispatch = async () => {
    if (!filters.date) {
      return setMessage("Please select date");
    }

    try {
      setLoading(true);

      let url = `http://localhost:8000/admin/dispatch?date=${filters.date}`;

      if (filters.route_id) {
        url += `&route_id=${filters.route_id}`;
      }

      if (filters.status) {
        url += `&status=${filters.status}`;
      }

      const res = await fetch(url, {
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
        },
      });

      if (!res.ok) throw new Error("Failed to fetch dispatch");

      const data = await res.json();
      setTrips(data);

    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // REDIRECT TO OVERRIDE
  // -------------------------
  const goToOverride = (tripId) => {
    // You can pass tripId via query params if needed
    window.location.href = `/override?trip_id=${tripId}`;
  };

  // -------------------------
  // STATUS COLOR
  // -------------------------
  const getStatusColor = (status) => {
    if (status === "delayed") return "text-red-600";
    if (status === "completed") return "text-green-600";
    if (status === "scheduled") return "text-gray-600";
    return "";
  };

  // -------------------------
  // UI
  // -------------------------
  return (
    <div className="p-6 space-y-8">

      <h1 className="text-2xl font-bold">Dispatch Panel</h1>

      {/* FILTERS */}
      <div className="bg-white p-4 shadow rounded flex flex-wrap gap-4">

        <input
          type="date"
          value={filters.date}
          onChange={(e) =>
            setFilters({ ...filters, date: e.target.value })
          }
          className="border p-2"
        />

        <select
          value={filters.route_id}
          onChange={(e) =>
            setFilters({ ...filters, route_id: e.target.value })
          }
          className="border p-2"
        >
          <option value="">All Routes</option>
          {routes.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>

        <select
          value={filters.status}
          onChange={(e) =>
            setFilters({ ...filters, status: e.target.value })
          }
          className="border p-2"
        >
          <option value="">All Status</option>
          <option value="scheduled">Scheduled</option>
          <option value="delayed">Delayed</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>

        <button
          onClick={fetchDispatch}
          className="bg-blue-600 text-white px-4"
        >
          Load
        </button>

      </div>

      {/* TABLE */}
      <div className="bg-white p-6 shadow rounded">

        {loading && <p>Loading...</p>}

        <table className="w-full border text-center">
          <thead className="bg-gray-100">
            <tr>
              <th>Trip ID</th>
              <th>Time</th>
              <th>Route</th>
              <th>Driver</th>
              <th>Bus</th>
              <th>Delay (min)</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {trips.map((t) => (
              <tr key={t.id} className="border-t">

                <td>{t.id}</td>
                <td>{t.start_time}</td>
                <td>{t.route_name}</td>
                <td>{t.driver_name}</td>
                <td>{t.bus_code}</td>

                <td className={t.delay_minutes > 0 ? "text-red-600" : ""}>
                  {t.delay_minutes || 0}
                </td>

                <td className={getStatusColor(t.status)}>
                  {t.status}
                </td>

                <td>
                  <button
                    onClick={() => goToOverride(t.id)}
                    className="bg-red-600 text-white px-2 py-1"
                  >
                    Override
                  </button>
                </td>

              </tr>
            ))}
          </tbody>
        </table>

        {trips.length === 0 && !loading && (
          <p className="text-gray-500 mt-4">
            No trips found
          </p>
        )}
      </div>

      {message && (
        <p className="text-purple-600">{message}</p>
      )}

    </div>
  );
}

export default DispatchPage;