import React, { useState } from "react";

function RoutesDataFeed() {

  const [newRoute, setNewRoute] = useState({
    route_short_name: "",
    route_long_name: "",
    stops: ""
  });

  const [searchId, setSearchId] = useState("");
  const [routeData, setRouteData] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);


  // Convert comma string to integer array
  const parseStops = (stopsString) => {
    return stopsString
      .split(",")
      .map((id) => parseInt(id.trim()))
      .filter((id) => !isNaN(id));
  };


  // ---------------------
  // ADD ROUTE
  // ---------------------
  const addRoute = async () => {
    try {
      setLoading(true);

      const res = await fetch("http://localhost:8000/admin/routes", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify({
          route_short_name: newRoute.route_short_name,
          route_long_name: newRoute.route_long_name,
          stops: parseStops(newRoute.stops)
        })
      });

      if (!res.ok) throw new Error("Failed to create route");

      setMessage("Route created successfully!");
      setNewRoute({ route_short_name: "", route_long_name: "", stops: "" });

    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  };


  // ---------------------
  // SEARCH ROUTE
  // ---------------------
  const searchRoute = async () => {
    try {
      setLoading(true);

      const res = await fetch(
        `http://localhost:8000/admin/routes/${searchId}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`
          }
        }
      );

      if (!res.ok) throw new Error("Route not found");

      const data = await res.json();
      setRouteData({
        ...data,
        stops: data.stops.join(", ")
      });

      setMessage("");

    } catch (err) {
      setRouteData(null);
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  };


  // ---------------------
  // UPDATE ROUTE
  // ---------------------
  const updateRoute = async () => {
    try {
      const res = await fetch(
        `http://localhost:8000/admin/routes/${routeData.route_id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`
          },
          body: JSON.stringify({
            route_short_name: routeData.route_short_name,
            route_long_name: routeData.route_long_name,
            stops: parseStops(routeData.stops)
          })
        }
      );

      if (!res.ok) throw new Error("Update failed");

      setMessage("Route updated successfully!");

    } catch (err) {
      setMessage(err.message);
    }
  };


  // ---------------------
  // DELETE ROUTE
  // ---------------------
  const deleteRoute = async () => {
    try {
      const res = await fetch(
        `http://localhost:8000/admin/routes/${routeData.route_id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`
          }
        }
      );

      if (!res.ok) throw new Error("Delete failed");

      setRouteData(null);
      setMessage("Route deleted successfully!");

    } catch (err) {
      setMessage(err.message);
    }
  };


  // ---------------------
  // UI
  // ---------------------
  return (
    <div className="p-6 space-y-6">

      <h1 className="text-2xl font-bold">Routes Management</h1>

      {/* ADD ROUTE */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">Add Route</h2>

        <input
          placeholder="Short Name"
          value={newRoute.route_short_name}
          onChange={(e) => setNewRoute({ ...newRoute, route_short_name: e.target.value })}
          className="border p-2 mr-2"
        />

        <input
          placeholder="Long Name"
          value={newRoute.route_long_name}
          onChange={(e) => setNewRoute({ ...newRoute, route_long_name: e.target.value })}
          className="border p-2 mr-2"
        />

        <input
          placeholder="Stops (comma separated IDs)"
          value={newRoute.stops}
          onChange={(e) => setNewRoute({ ...newRoute, stops: e.target.value })}
          className="border p-2 mr-2"
        />

        <button
          onClick={addRoute}
          className="bg-purple-600 text-white px-4 py-2 rounded"
        >
          Add
        </button>
      </div>


      {/* SEARCH ROUTE */}
      <div className="bg-white p-6 shadow rounded">

        <h2 className="font-semibold mb-4">Search Route by ID</h2>

        <input
          type="number"
          placeholder="Route ID"
          value={searchId}
          onChange={(e) => setSearchId(e.target.value)}
          className="border p-2 mr-2"
        />

        <button
          onClick={searchRoute}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          Search
        </button>

        {routeData && (
          <div className="mt-4 space-y-2">

            <input
              value={routeData.route_short_name}
              onChange={(e) =>
                setRouteData({ ...routeData, route_short_name: e.target.value })
              }
              className="border p-2 block"
            />

            <input
              value={routeData.route_long_name}
              onChange={(e) =>
                setRouteData({ ...routeData, route_long_name: e.target.value })
              }
              className="border p-2 block"
            />

            <input
              value={routeData.stops}
              onChange={(e) =>
                setRouteData({ ...routeData, stops: e.target.value })
              }
              className="border p-2 block"
            />

            <div className="flex gap-4 mt-2">
              <button
                onClick={updateRoute}
                className="bg-green-600 text-white px-4 py-2 rounded"
              >
                Update
              </button>

              <button
                onClick={deleteRoute}
                className="bg-red-600 text-white px-4 py-2 rounded"
              >
                Delete
              </button>
            </div>

          </div>
        )}

        {message && (
          <p className="mt-4 text-purple-700">{message}</p>
        )}

      </div>

    </div>
  );
}

export default RoutesDataFeed;