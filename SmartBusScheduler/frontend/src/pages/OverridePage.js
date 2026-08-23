import React, { useEffect, useState } from "react";
import AdminLayout from "./AdminLayout";

function OverridePage() {
  const [date, setDate] = useState("");
  const [trips, setTrips] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(null);

  const [drivers, setDrivers] = useState([]);
  const [buses, setBuses] = useState([]);

  const [overrideData, setOverrideData] = useState({
    new_driver_id: "",
    new_bus_id: "",
    new_start_time: "",
    reason: "",
  });

  const [history, setHistory] = useState([]);
  const [message, setMessage] = useState("");

  const token = sessionStorage.getItem("token");

  // -------------------------
  // FETCH INITIAL DATA
  // -------------------------
  const fetchInit = async () => {
    try {
      const [d, b, h] = await Promise.all([
        fetch("http://localhost:8000/admin/drivers", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("http://localhost:8000/admin/buses", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("http://localhost:8000/admin/dispatch/overrides", {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (!d.ok || !b.ok || !h.ok) {
        throw new Error("Failed to fetch initial data");
      }

      setDrivers(await d.json());
      setBuses(await b.json());
      setHistory(await h.json());
    } catch (error) {
      setMessage("Failed to load data");
    }
  };

  useEffect(() => {
    fetchInit();
  }, []);

  // -------------------------
  // FETCH TRIPS BY DATE
  // -------------------------
  const fetchTrips = async () => {
    if (!date) return;

    try {
      const res = await fetch(
        `http://localhost:8000/admin/dispatch?date=${date}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!res.ok) throw new Error("Failed to fetch trips");

      const data = await res.json();
      setTrips(data);
    } catch {
      setMessage("Failed to fetch trips");
    }
  };

  // -------------------------
  // APPLY OVERRIDE
  // -------------------------
  const applyOverride = async () => {
    if (!selectedTrip) {
      setMessage("Select a trip");
      return;
    }

    try {
      // Normal overrides (driver, bus, time)
      if (
        overrideData.new_driver_id ||
        overrideData.new_bus_id ||
        overrideData.new_start_time
      ) {
        const res = await fetch(
          "http://localhost:8000/admin/dispatch/overrides",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              trip_id: selectedTrip.id,
              new_driver_id: overrideData.new_driver_id || null,
              new_bus_id: overrideData.new_bus_id || null,
              new_start_time: overrideData.new_start_time || null,
              reason: overrideData.reason,
            }),
          }
        );

        if (!res.ok) throw new Error("Override failed");
      }

      setMessage("Override applied successfully!");
      setSelectedTrip(null);
      setOverrideData({
        new_driver_id: "",
        new_bus_id: "",
        new_start_time: "",
        reason: "",
      });

      fetchTrips();
      fetchInit();
    } catch (error) {
      setMessage(error.message || "Operation failed");
    }
  };

  // -------------------------
  // UI
  // -------------------------
  return (
    <AdminLayout>
      <div className="p-6 space-y-8">
      <h1 className="text-2xl font-bold">Override Management</h1>

      {/* SELECT TRIP */}
      <div className="bg-[#E6F1FB] p-6 rounded-xl shadow-md">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Select Trip
      </h2>

      <div className="flex flex-col md:flex-row gap-3 mb-4">

        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="input"
        />

        <button
          onClick={fetchTrips}
          className="px-4 py-2 bg-[#0C447C] text-white rounded-lg hover:bg-[#0A3A6A] transition"
        >
          Load Trips
        </button>
      </div>

      <table className="w-full text-sm text-gray-700">
        <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
          <tr>
            <th className="px-4 py-3 text-left">Route</th>
            <th className="px-4 py-3">Time</th>
            <th className="px-4 py-3">Driver</th>
            <th className="px-4 py-3">Bus</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3 text-center">Action</th>
          </tr>
        </thead>

        <tbody className="divide-y">
          {trips.map((t) => (
            <tr key={t.id} className="hover:bg-gray-50 transition">

              <td className="px-4 py-3 font-semibold text-gray-800">
                {t.route_name}
              </td>

              <td className="px-4 py-3">{t.start_time}</td>
              <td className="px-4 py-3">{t.driver_name}</td>
              <td className="px-4 py-3">{t.bus_code}</td>

              {/* STATUS BADGE */}
              <td className="px-4 py-3">
                <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-700">
                  {t.status}
                </span>
              </td>

              <td className="px-4 py-3 flex justify-center">
                <button
                  onClick={() => {
                    setSelectedTrip(t);
                    setOverrideData({
                      new_driver_id: "",
                      new_bus_id: "",
                      new_start_time: t.start_time,
                      reason: "",
                    });
                  }}
                  className="px-3 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 transition"
                >
                  Select
                </button>
              </td>
            </tr>
          ))}

          {trips.length === 0 && (
            <tr>
              <td colSpan="6" className="text-center py-6 text-gray-400">
                No trips found
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>

      {/* APPLY OVERRIDE */}
      {selectedTrip && (
      <div className="fixed inset-0 z-50 flex items-center justify-center">

        {/* BACKDROP */}
        <div
          className="absolute inset-0 bg-black/40 backdrop-blur-sm"
          onClick={() => setSelectedTrip(null)}
        ></div>

        {/* MODAL */}
        <div className="relative bg-white w-full max-w-xl rounded-xl shadow-lg p-6">

          <h2 className="text-lg font-semibold mb-2">
            Apply Override
          </h2>

          <p className="text-sm text-gray-500 mb-4">
            {selectedTrip.route_name} • {selectedTrip.start_time}
          </p>

          <div className="grid grid-cols-2 gap-4">

            <select
              value={overrideData.new_driver_id}
              onChange={(e) =>
                setOverrideData({
                  ...overrideData,
                  new_driver_id: e.target.value,
                })
              }
              className="input"
            >
              <option value="">Select Driver</option>
              {drivers.map((d) => (
                <option key={d.user_id} value={d.user_id}>
                  {d.name}
                </option>
              ))}
            </select>

            <select
              value={overrideData.new_bus_id}
              onChange={(e) =>
                setOverrideData({
                  ...overrideData,
                  new_bus_id: e.target.value,
                })
              }
              className="input"
            >
              <option value="">Select Bus</option>
              {buses.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.code}
                </option>
              ))}
            </select>

            <input
              type="time"
              value={overrideData.new_start_time}
              onChange={(e) =>
                setOverrideData({
                  ...overrideData,
                  new_start_time: e.target.value,
                })
              }
              className="input"
            />

            <input
              placeholder="Reason"
              value={overrideData.reason}
              onChange={(e) =>
                setOverrideData({
                  ...overrideData,
                  reason: e.target.value,
                })
              }
              className="input col-span-2"
            />
          </div>

          <div className="mt-6 flex justify-end gap-3">
            <button
              onClick={() => setSelectedTrip(null)}
              className="px-4 py-2 border rounded-lg"
            >
              Cancel
            </button>

            <button
              onClick={() => {
                applyOverride();
                setSelectedTrip(null);
              }}
              className="px-5 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
            >
              Apply Override
            </button>
          </div>
        </div>
      </div>
    )}

      {/* HISTORY */}
      <div className="bg-white p-6 rounded-xl shadow-md">

      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Override History
      </h2>

      <table className="w-full bg-[#E6F1FB] text-sm text-gray-700">
        <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
          <tr>
            <th className="px-4 py-3">Trip</th>
            <th className="px-4 py-3">Old Driver</th>
            <th className="px-4 py-3">New Driver</th>
            <th className="px-4 py-3">Old Bus</th>
            <th className="px-4 py-3">New Bus</th>
            <th className="px-4 py-3">Reason</th>
            <th className="px-4 py-3">Timestamp</th>
          </tr>
        </thead>

        <tbody className="divide-y">
          {history.map((h) => (
            <tr key={h.id} className="hover:bg-gray-50 transition">
              <td className="px-4 py-3">{h.trip_id}</td>
              <td className="px-4 py-3">{h.old_driver_id}</td>
              <td className="px-4 py-3">{h.new_driver_id}</td>
              <td className="px-4 py-3">{h.old_bus_id}</td>
              <td className="px-4 py-3">{h.new_bus_id}</td>
              <td className="px-4 py-3">{h.reason || "-"}</td>
              <td className="px-4 py-3 text-xs text-gray-500">
                {new Date(h.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>

      {message && <p className="text-purple-600">{message}</p>}
    </div>
    </AdminLayout>
  );
}

export default OverridePage;