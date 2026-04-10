import React, { useEffect, useState } from "react";

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
    new_status: "",
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

      // Live status update
      if (overrideData.new_status) {
        const res = await fetch(
          `http://localhost:8000/admin/dispatch/${selectedTrip.id}/status`,
          {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              status: overrideData.new_status,
            }),
          }
        );

        if (!res.ok) throw new Error("Status update failed");
      }

      setMessage("Override applied successfully!");
      setSelectedTrip(null);
      setOverrideData({
        new_driver_id: "",
        new_bus_id: "",
        new_start_time: "",
        new_status: "",
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
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-bold">Override Management</h1>

      {/* SELECT TRIP */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">Select Trip</h2>

        <div className="flex gap-4">
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="border p-2"
          />

          <button
            onClick={fetchTrips}
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            Load Trips
          </button>
        </div>

        <table className="w-full mt-4 border text-center">
          <thead className="bg-gray-100">
            <tr>
              <th>Route</th>
              <th>Time</th>
              <th>Driver</th>
              <th>Bus</th>
              <th>Status</th>
              <th>Select</th>
            </tr>
          </thead>

          <tbody>
            {trips.map((t) => (
              <tr key={t.id} className="border-t">
                <td>{t.route_name}</td>
                <td>{t.start_time}</td>
                <td>{t.driver_name}</td>
                <td>{t.bus_code}</td>
                <td>{t.status}</td>
                <td>
                  <button
                    onClick={() => {
                      setSelectedTrip(t);
                      setOverrideData({
                        new_driver_id: "",
                        new_bus_id: "",
                        new_start_time: t.start_time,
                        new_status: t.status,
                        reason: "",
                      });
                    }}
                    className="bg-purple-600 text-white px-3 py-1 rounded"
                  >
                    Select
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* APPLY OVERRIDE */}
      {selectedTrip && (
        <div className="bg-white p-6 shadow rounded">
          <h2 className="font-semibold mb-4">Apply Override</h2>

          <p className="mb-2">
            <strong>Route:</strong> {selectedTrip.route_name} |{" "}
            <strong>Time:</strong> {selectedTrip.start_time}
          </p>

          <div className="grid grid-cols-2 gap-4">
            {/* Driver */}
            <select
              value={overrideData.new_driver_id}
              onChange={(e) =>
                setOverrideData({
                  ...overrideData,
                  new_driver_id: e.target.value,
                })
              }
              className="border p-2"
            >
              <option value="">Select Driver</option>
              {drivers.map((d) => (
                <option key={d.user_id} value={d.user_id}>
                  {d.name}
                </option>
              ))}
            </select>

            {/* Bus */}
            <select
              value={overrideData.new_bus_id}
              onChange={(e) =>
                setOverrideData({
                  ...overrideData,
                  new_bus_id: e.target.value,
                })
              }
              className="border p-2"
            >
              <option value="">Select Bus</option>
              {buses.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.code}
                </option>
              ))}
            </select>

            {/* Time Override */}
            <input
              type="time"
              value={overrideData.new_start_time}
              onChange={(e) =>
                setOverrideData({
                  ...overrideData,
                  new_start_time: e.target.value,
                })
              }
              className="border p-2"
            />

            {/* Status Update */}
            <select
              value={overrideData.new_status}
              onChange={(e) =>
                setOverrideData({
                  ...overrideData,
                  new_status: e.target.value,
                })
              }
              className="border p-2"
            >
              <option value="">Select Status</option>
              <option value="SCHEDULED">Scheduled</option>
              <option value="DELAYED">Delayed</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>

            {/* Reason */}
            <input
              placeholder="Reason"
              value={overrideData.reason}
              onChange={(e) =>
                setOverrideData({
                  ...overrideData,
                  reason: e.target.value,
                })
              }
              className="border p-2 col-span-2"
            />
          </div>

          <button
            onClick={applyOverride}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded"
          >
            Apply Override
          </button>
        </div>
      )}

      {/* HISTORY */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">Override History</h2>

        <table className="w-full border text-center">
          <thead className="bg-gray-100">
            <tr>
              <th>Trip</th>
              <th>Old Driver</th>
              <th>New Driver</th>
              <th>Old Bus</th>
              <th>New Bus</th>
              <th>Old Time</th>
              <th>New Time</th>
              <th>Reason</th>
              <th>Time</th>
            </tr>
          </thead>

          <tbody>
            {history.map((h) => (
              <tr key={h.id} className="border-t">
                <td>{h.trip_id}</td>
                <td>{h.old_driver_id}</td>
                <td>{h.new_driver_id}</td>
                <td>{h.old_bus_id}</td>
                <td>{h.new_bus_id}</td>
                <td>{h.old_start_time || "-"}</td>
                <td>{h.new_start_time || "-"}</td>
                <td>{h.reason || "-"}</td>
                <td>{new Date(h.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {message && <p className="text-purple-600">{message}</p>}
    </div>
  );
}

export default OverridePage;