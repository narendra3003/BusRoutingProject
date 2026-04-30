import React, { useEffect, useState } from "react";
import AdminLayout from "./AdminLayout";
function RouteBuilder() {
  const [routes, setRoutes] = useState([]);
  const [stops, setStops] = useState([]);

  const [selectedRoute, setSelectedRoute] = useState("");
  const [routeStops, setRouteStops] = useState([]);

  const [search, setSearch] = useState("");
  const [message, setMessage] = useState("");

  // -------------------------
  // FETCH ROUTES
  // -------------------------
  const fetchRoutes = async () => {
    const res = await fetch("http://localhost:8000/admin/routes",
        {
            headers: {
                Authorization: `Bearer ${sessionStorage.getItem("token")}`
            }
        }
    );
    const data = await res.json();
    setRoutes(data);
  };

  // -------------------------
  // FETCH STOPS
  // -------------------------
  const fetchStops = async () => {
    const res = await fetch("http://localhost:8000/stops");
    const data = await res.json();
    setStops(data);
  };

  // -------------------------
  // FETCH ROUTE STOPS
  // -------------------------
  const fetchRouteStops = async (routeId) => {
    if (!routeId) return;

    const res = await fetch(
      `http://localhost:8000/admin/routes/${routeId}/stops`,{
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("token")}`
        }
      }
    );

    /*
    RESPONSE:
    [
      { stop_id: 1, seq: 1, name: "A" },
      { stop_id: 5, seq: 2, name: "B" }
    ]
    */

    const data = await res.json();

    setRouteStops(data.map((s) => s.stop_id));
  };

  useEffect(() => {
    fetchRoutes();
    fetchStops();
  }, []);

  useEffect(() => {
    fetchRouteStops(selectedRoute);
  }, [selectedRoute]);

  // -------------------------
  // ADD STOP
  // -------------------------
  const addStop = (id) => {
    if (routeStops.includes(id)) return;
    setRouteStops([...routeStops, id]);
  };

  // -------------------------
  // REMOVE STOP
  // -------------------------
  const removeStop = (id) => {
    setRouteStops(routeStops.filter((s) => s !== id));
  };

  // -------------------------
  // MOVE UP
  // -------------------------
  const moveUp = (index) => {
    if (index === 0) return;

    const newList = [...routeStops];
    [newList[index - 1], newList[index]] = [
      newList[index],
      newList[index - 1],
    ];

    setRouteStops(newList);
  };

  // -------------------------
  // MOVE DOWN
  // -------------------------
  const moveDown = (index) => {
    if (index === routeStops.length - 1) return;

    const newList = [...routeStops];
    [newList[index], newList[index + 1]] = [
      newList[index + 1],
      newList[index],
    ];

    setRouteStops(newList);
  };

  // -------------------------
  // SAVE ROUTE STOPS
  // -------------------------
  const saveRouteStops = async () => {
    if (!selectedRoute) return setMessage("Select a route");

    try {
      await fetch("http://localhost:8000/admin/route-stops/bulk", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          route_id: selectedRoute,
          stops: routeStops,
        }),

        /*
        REQUEST:
        {
          route_id: "101_UP",
          stops: [1, 5, 8, 10]
        }

        BACKEND:
        - Deletes old entries
        - Inserts with seq = index + 1
        */
      });

      setMessage("Route stops saved!");
    } catch {
      setMessage("Save failed");
    }
  };

  // -------------------------
  // FILTERED STOPS
  // -------------------------
  const filteredStops = stops.filter((s) =>
    s.name.toLowerCase().includes(search.toLowerCase())
  );

  const getStopName = (id) => {
    const s = stops.find((x) => x.id === id);
    return s ? s.name : id;
  };

  // -------------------------
  // UI
  // -------------------------
  return (
    <AdminLayout>
      <div className="p-6 space-y-6">

        {/* HEADER */}
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            Route Builder
          </h1>
          <p className="text-sm text-gray-500">
            Create and manage ordered stops for each route
          </p>
        </div>

        {/* SELECT ROUTE */}
        <div className="bg-white p-5 rounded-xl shadow-md">
          <label className="block text-sm font-medium text-gray-600 mb-2">
            Select Route
          </label>
          <select
            value={selectedRoute}
            onChange={(e) => setSelectedRoute(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Select Route</option>
            {routes.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name} ({r.id})
              </option>
            ))}
          </select>
        </div>

        {/* MAIN GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* LEFT: ALL STOPS */}
          <div className="bg-white p-5 rounded-xl shadow-md">
            <h2 className="text-md font-semibold text-gray-800 mb-3">
              All Stops
            </h2>

            <input
              placeholder="Search stops..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />

            <div className="max-h-96 overflow-y-auto space-y-2 pr-1">
              {filteredStops.map((s) => (
                <div
                  key={s.id}
                  className="flex justify-between items-center px-3 py-2 border rounded-lg hover:bg-gray-50 transition"
                >
                  <span className="text-sm text-gray-700">
                    {s.name}
                  </span>

                  <button
                    onClick={() => addStop(s.id)}
                    className="px-3 py-1 bg-blue-500 text-white text-xs rounded-md hover:bg-blue-600 transition active:scale-95"
                  >
                    + Add
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* RIGHT: SELECTED STOPS */}
          <div className="bg-white p-5 rounded-xl shadow-md">
            <h2 className="text-md font-semibold text-gray-800 mb-3">
              Route Stops (Ordered)
            </h2>

            <div className="max-h-96 overflow-y-auto space-y-2 pr-1">
              {routeStops.map((id, index) => (
                <div
                  key={id}
                  className="flex justify-between items-center px-3 py-2 border rounded-lg hover:bg-gray-50 transition"
                >
                  <span className="text-sm text-gray-800 font-medium">
                    {index + 1}. {getStopName(id)}
                  </span>

                  <div className="flex gap-2">
                    <button
                      onClick={() => moveUp(index)}
                      className="px-2 py-1 text-xs bg-gray-200 rounded hover:bg-gray-300 transition"
                    >
                      ↑
                    </button>

                    <button
                      onClick={() => moveDown(index)}
                      className="px-2 py-1 text-xs bg-gray-200 rounded hover:bg-gray-300 transition"
                    >
                      ↓
                    </button>

                    <button
                      onClick={() => removeStop(id)}
                      className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}

              {routeStops.length === 0 && (
                <p className="text-sm text-gray-400 text-center py-4">
                  No stops added yet
                </p>
              )}
            </div>

            <button
              onClick={saveRouteStops}
              className="mt-5 w-full py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition active:scale-95"
            >
              Save Route Stops
            </button>
          </div>
        </div>

        {/* MESSAGE */}
        {message && (
          <p className="text-sm text-green-600 font-medium">
            {message}
          </p>
        )}
      </div>
    </AdminLayout>
  );
}

export default RouteBuilder;