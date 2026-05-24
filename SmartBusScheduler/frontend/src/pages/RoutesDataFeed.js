import React, { useEffect, useState } from "react";
import AdminLayout from "./AdminLayout";
import EditRouteModal from "./EditRouteModal";

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
    <AdminLayout>
    <div className="p-6 space-y-8">

      <h1 className="text-2xl font-bold">Routes Management</h1>

      <div className="bg-[#E6F1FB] p-6 rounded-xl shadow-md">
  
  {/* HEADER */}
  <div className="mb-5">
    <h2 className="text-lg font-semibold text-gray-800">
      Create Route
    </h2>
    <p className="text-sm text-gray-500">
      Add a new route to the system
    </p>
  </div>

  {/* FORM GRID */}
  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

    {/* ROUTE ID */}
    <div>
      <label className="block text-sm font-medium text-gray-600 mb-1">
        Route ID
      </label>
      <input
        placeholder="e.g. 101_UP"
        value={newRoute.id}
        onChange={(e) =>
          setNewRoute({ ...newRoute, id: e.target.value })
        }
        className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0C447C]"
      />
    </div>

    {/* ROUTE NAME */}
    <div>
      <label className="block text-sm font-medium text-gray-600 mb-1">
        Route Name
      </label>
      <input
        placeholder="Enter route name"
        value={newRoute.name}
        onChange={(e) =>
          setNewRoute({ ...newRoute, name: e.target.value })
        }
        className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0C447C]"
      />
    </div>

    {/* START STOP */}
    <div>
      <label className="block text-sm font-medium text-gray-600 mb-1">
        Start Stop
      </label>
      <select
        value={newRoute.start_stop_id}
        onChange={(e) =>
          setNewRoute({ ...newRoute, start_stop_id: e.target.value })
        }
        className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0C447C]"
      >
        <option value="">Select Start Stop</option>
        {stops.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>
    </div>

    {/* END STOP */}
    <div>
      <label className="block text-sm font-medium text-gray-600 mb-1">
        End Stop
      </label>
      <select
        value={newRoute.end_stop_id}
        onChange={(e) =>
          setNewRoute({ ...newRoute, end_stop_id: e.target.value })
        }
        className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0C447C]"
      >
        <option value="">Select End Stop</option>
        {stops.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>
    </div>
  </div>

  {/* ACTION BUTTON */}
  <div className="mt-6 flex justify-end">
    <button
      onClick={addRoute}
      className="px-5 py-2 bg-[#0C447C] text-white text-sm font-medium rounded-lg shadow-sm hover:bg-[#0A3A6A] transition active:scale-95"
    >
      + Create Route
    </button>
  </div>
</div>

      {/* ROUTES TABLE */}
      <div className="bg-[#E6F1FB] a p-6 shadow rounded">
        <h2 className="font-semibold mb-4">All Routes</h2>

        <input
          placeholder="Search routes..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border p-2 mb-4 w-full"
        />

        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <table className="w-full text-sm text-gray-700">

            {/* HEADER */}
            <thead className="bg-gray-50 text-gray-600 uppercase text-xs tracking-wider">
              <tr>
                <th className="px-6 py-3 text-left">ID</th>
                <th className="px-6 py-3 text-left">Route Name</th>
                <th className="px-6 py-3 text-left">Start</th>
                <th className="px-6 py-3 text-left">End</th>
                <th className="px-6 py-3 text-center">Actions</th>
              </tr>
            </thead>

            {/* BODY */}
            <tbody className="divide-y">
              {filteredRoutes.map((r) => (
                <tr
                  key={r.id}
                  className="hover:bg-gray-50 transition duration-150"
                >
                  <td className="px-6 py-4 font-medium text-gray-900">
                    #{r.id}
                  </td>

                  <td className="px-6 py-4 font-semibold text-gray-800">
                    {r.name}
                  </td>

                  <td className="px-6 py-4">
                    {r.start_stop_name || r.start_stop_id}
                  </td>

                  <td className="px-6 py-4">
                    {r.end_stop_name || r.end_stop_id}
                  </td>

                  {/* ACTIONS */}
                  <td className="px-6 py-4 flex justify-center gap-2">
                    <button
                      onClick={() => setSelectedRoute(r)}
                      className="px-3 py-1.5 bg-yellow-400 text-white text-xs font-medium rounded-md hover:bg-yellow-500 transition active:scale-95"
                    >
                      Edit
                    </button>

                    <button
                      onClick={() => deleteRoute(r.id)}
                      className="px-3 py-1.5 bg-red-500 text-white text-xs font-medium rounded-md hover:bg-red-600 transition active:scale-95"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>

      {/* EDIT */}
      <EditRouteModal
      selectedRoute={selectedRoute}
      setSelectedRoute={setSelectedRoute}
      updateRoute={updateRoute}
      stops={stops}
    />

      {message && <p className="text-purple-600">{message}</p>}
    </div>
    </AdminLayout>
  );
}

export default RoutesDataFeed;