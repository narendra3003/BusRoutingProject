import React, { useEffect, useState } from "react";

function RoutesDataFeed() {
  const [routes, setRoutes] = useState([]);
  const [stops, setStops] = useState([]);
  const [search, setSearch] = useState("");

  const [newRoute, setNewRoute] = useState({
    id: "",
    name: "",
    start_stop_id: "",
    end_stop_id: "",
  });

  const [selectedRoute, setSelectedRoute] = useState(null);

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // -------------------------
  // FETCH ROUTES
  // -------------------------
  const fetchRoutes = async () => {
    try {
      const res = await fetch("http://localhost:8000/admin/routes",{
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
        }
      });
      const data = await res.json();
      setRoutes(data);
    } catch {
      setMessage("Failed to fetch routes");
    }
  };

  // -------------------------
  // FETCH STOPS (for dropdown)
  // -------------------------
  const fetchStops = async () => {
    try {
      const res = await fetch("http://localhost:8000/stops");
      const data = await res.json();
      setStops(data);
    } catch {
      setMessage("Failed to fetch stops");
    }
  };

  useEffect(() => {
    fetchRoutes();
    fetchStops();
  }, []);

  // -------------------------
  // ADD ROUTE
  // -------------------------
  const addRoute = async () => {
    if (!newRoute.id || !newRoute.name || !newRoute.start_stop_id || !newRoute.end_stop_id) {
      return setMessage("All fields required");
    }

    try {
      setLoading(true);

      await fetch("http://localhost:8000/admin/routes", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
        },
        body: JSON.stringify(newRoute),

        /*
        REQUEST:
        {
          id: "101_UP",
          name: "Station A → Station B",
          start_stop_id: 1,
          end_stop_id: 10
        }

        RESPONSE:
        { success: true }
        */
      });

      setMessage("Route created!");
      setNewRoute({
        id: "",
        name: "",
        start_stop_id: "",
        end_stop_id: "",
      });

      fetchRoutes();
    } catch {
      setMessage("Failed to create route");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // UPDATE ROUTE
  // -------------------------
  const updateRoute = async () => {
    try {
      await fetch(
        `http://localhost:8000/admin/routes/${selectedRoute.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
          body: JSON.stringify(selectedRoute),
        }
      );

      setMessage("Updated!");
      setSelectedRoute(null);
      fetchRoutes();
    } catch {
      setMessage("Update failed");
    }
  };

  // -------------------------
  // DELETE ROUTE
  // -------------------------
  const deleteRoute = async (id) => {
    try {
      await fetch(`http://localhost:8000/admin/routes/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
        },
      });

      setMessage("Deleted!");
      fetchRoutes();
    } catch {
      setMessage("Delete failed");
    }
  };

  // -------------------------
  // FILTER
  // -------------------------
  const filteredRoutes = routes.filter((r) =>
    r.name.toLowerCase().includes(search.toLowerCase())
  );

  // -------------------------
  // UI
  // -------------------------
  return (
    <div className="p-6 space-y-8">

      <h1 className="text-2xl font-bold">Routes Management</h1>

      {/* ADD ROUTE */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">Create Route</h2>

        <div className="grid grid-cols-2 gap-4">

          <input
            placeholder="Route ID (e.g. 101_UP)"
            value={newRoute.id}
            onChange={(e) =>
              setNewRoute({ ...newRoute, id: e.target.value })
            }
            className="border p-2"
          />

          <input
            placeholder="Route Name"
            value={newRoute.name}
            onChange={(e) =>
              setNewRoute({ ...newRoute, name: e.target.value })
            }
            className="border p-2"
          />

          <select
            value={newRoute.start_stop_id}
            onChange={(e) =>
              setNewRoute({ ...newRoute, start_stop_id: e.target.value })
            }
            className="border p-2"
          >
            <option value="">Select Start Stop</option>
            {stops.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>

          <select
            value={newRoute.end_stop_id}
            onChange={(e) =>
              setNewRoute({ ...newRoute, end_stop_id: e.target.value })
            }
            className="border p-2"
          >
            <option value="">Select End Stop</option>
            {stops.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={addRoute}
          className="mt-4 bg-purple-600 text-white px-4 py-2 rounded"
        >
          Create Route
        </button>
      </div>

      {/* ROUTES TABLE */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">All Routes</h2>

        <input
          placeholder="Search routes..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border p-2 mb-4 w-full"
        />

        <table className="w-full border text-center">
          <thead className="bg-gray-100">
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Start</th>
              <th>End</th>
              <th>Distance</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {filteredRoutes.map((r) => (
              <tr key={r.id} className="border-t">
                <td>{r.id}</td>
                <td>{r.name}</td>
                <td>{r.start_stop_name || r.start_stop_id}</td>
                <td>{r.end_stop_name || r.end_stop_id}</td>
                <td>{r.distance_km || "-"}</td>

                <td className="space-x-2">
                  <button
                    onClick={() => setSelectedRoute(r)}
                    className="bg-yellow-500 text-white px-2 py-1"
                  >
                    Edit
                  </button>

                  <button
                    onClick={() => deleteRoute(r.id)}
                    className="bg-red-600 text-white px-2 py-1"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* EDIT */}
      {selectedRoute && (
        <div className="bg-white p-6 shadow rounded">
          <h2 className="font-semibold mb-4">Edit Route</h2>

          <div className="grid grid-cols-2 gap-4">

            <input
              value={selectedRoute.name}
              onChange={(e) =>
                setSelectedRoute({ ...selectedRoute, name: e.target.value })
              }
              className="border p-2"
            />

            <select
              value={selectedRoute.start_stop_id}
              onChange={(e) =>
                setSelectedRoute({
                  ...selectedRoute,
                  start_stop_id: e.target.value,
                })
              }
              className="border p-2"
            >
              {stops.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>

            <select
              value={selectedRoute.end_stop_id}
              onChange={(e) =>
                setSelectedRoute({
                  ...selectedRoute,
                  end_stop_id: e.target.value,
                })
              }
              className="border p-2"
            >
              {stops.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={updateRoute}
            className="mt-4 bg-green-600 text-white px-4 py-2"
          >
            Save Changes
          </button>
        </div>
      )}

      {message && <p className="text-purple-600">{message}</p>}
    </div>
  );
}

export default RoutesDataFeed;