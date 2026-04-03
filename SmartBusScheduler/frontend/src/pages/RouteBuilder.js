import React, { useEffect, useState } from "react";

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
    <div className="p-6 space-y-6">

      <h1 className="text-2xl font-bold">Route Builder</h1>

      {/* SELECT ROUTE */}
      <div className="bg-white p-4 shadow rounded">
        <select
          value={selectedRoute}
          onChange={(e) => setSelectedRoute(e.target.value)}
          className="border p-2 w-full"
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
      <div className="grid grid-cols-2 gap-6">

        {/* LEFT: ALL STOPS */}
        <div className="bg-white p-4 shadow rounded">
          <h2 className="font-semibold mb-2">All Stops</h2>

          <input
            placeholder="Search stops..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border p-2 w-full mb-3"
          />

          <div className="max-h-96 overflow-y-auto space-y-2">
            {filteredStops.map((s) => (
              <div
                key={s.id}
                className="flex justify-between border p-2 rounded"
              >
                <span>{s.name}</span>

                <button
                  onClick={() => addStop(s.id)}
                  className="bg-blue-600 text-white px-2"
                >
                  Add →
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT: SELECTED STOPS */}
        <div className="bg-white p-4 shadow rounded">
          <h2 className="font-semibold mb-2">Route Stops (Ordered)</h2>

          <div className="max-h-96 overflow-y-auto space-y-2">
            {routeStops.map((id, index) => (
              <div
                key={id}
                className="flex justify-between items-center border p-2 rounded"
              >
                <span>
                  {index + 1}. {getStopName(id)}
                </span>

                <div className="space-x-2">
                  <button
                    onClick={() => moveUp(index)}
                    className="bg-gray-300 px-2"
                  >
                    ↑
                  </button>

                  <button
                    onClick={() => moveDown(index)}
                    className="bg-gray-300 px-2"
                  >
                    ↓
                  </button>

                  <button
                    onClick={() => removeStop(id)}
                    className="bg-red-500 text-white px-2"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={saveRouteStops}
            className="mt-4 bg-green-600 text-white px-4 py-2 w-full"
          >
            Save Route Stops
          </button>
        </div>
      </div>

      {message && <p className="text-purple-600">{message}</p>}
    </div>
  );
}

export default RouteBuilder;