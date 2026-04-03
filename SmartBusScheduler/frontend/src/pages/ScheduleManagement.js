import React, { useEffect, useState } from "react";

function ScheduleManagement() {
  const [routes, setRoutes] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [buses, setBuses] = useState([]);

  const [schedule, setSchedule] = useState([]);

  const [filters, setFilters] = useState({
    date: "",
    route_id: "",
  });

  const [newTrip, setNewTrip] = useState({
    route_id: "",
    trip_date: "",
    start_time: "",
    driver_id: "",
    bus_id: "",
  });

  const [selectedTrip, setSelectedTrip] = useState(null);

  const [message, setMessage] = useState("");

  // -------------------------
  // FETCH DATA
  // -------------------------
  const fetchInit = async () => {
    try {
      const [r, d, b] = await Promise.all([
        fetch("http://localhost:8000/admin/routes", {
          headers: {
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
        }),
        fetch("http://localhost:8000/admin/drivers", {
          headers: {
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
        }),
        fetch("http://localhost:8000/admin/buses", {
          headers: {
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
        }),
      ]);

      setRoutes(await r.json());
      setDrivers(await d.json());
      setBuses(await b.json());
    } catch {
      setMessage("Failed to load data");
    }
  };

  useEffect(() => {
    fetchInit();
  }, []);

  // -------------------------
  // CREATE TRIP
  // -------------------------
  const createTrip = async () => {
    if (
      !newTrip.route_id ||
      !newTrip.trip_date ||
      !newTrip.start_time ||
      !newTrip.driver_id ||
      !newTrip.bus_id
    ) {
      return setMessage("All fields required");
    }

    try {
      await fetch("http://localhost:8000/admin/schedule", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
        },
        body: JSON.stringify(newTrip),

        /*
        REQUEST:
        {
          route_id,
          trip_date,
          start_time,
          driver_id,
          bus_id
        }
        */
      });

      setMessage("Trip created!");
      setNewTrip({
        route_id: "",
        trip_date: "",
        start_time: "",
        driver_id: "",
        bus_id: "",
      });

      fetchSchedule();
    } catch {
      setMessage("Create failed");
    }
  };

  // -------------------------
  // FETCH SCHEDULE
  // -------------------------
  const fetchSchedule = async () => {
    try {
      let url = "";

      if (filters.date) {
        url = `http://localhost:8000/schedule/date/${filters.date}`;
      } else if (filters.route_id) {
        url = `http://localhost:8000/schedule/route/${filters.route_id}`;
      } else {
        return;
      }

      const res = await fetch(url);
      const data = await res.json();

      setSchedule(data);

      /*
      RESPONSE:
      [
        {
          id: 1,
          start_time: "10:00",
          route_name: "...",
          driver_name: "...",
          bus_code: "...",
          status: "scheduled"
        }
      ]
      */
    } catch {
      setMessage("Failed to fetch schedule");
    }
  };

  // -------------------------
  // UPDATE TRIP
  // -------------------------
  const updateTrip = async () => {
    try {
      await fetch(
        `http://localhost:8000/admin/schedule/${selectedTrip.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
          body: JSON.stringify(selectedTrip),
        }
      );

      setMessage("Updated!");
      setSelectedTrip(null);
      fetchSchedule();
    } catch {
      setMessage("Update failed");
    }
  };

  // -------------------------
  // UI
  // -------------------------
  return (
    <div className="p-6 space-y-8">

      <h1 className="text-2xl font-bold">Schedule Management</h1>

      {/* CREATE TRIP */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">Create Trip</h2>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">

          <select
            value={newTrip.route_id}
            onChange={(e) =>
              setNewTrip({ ...newTrip, route_id: e.target.value })
            }
            className="border p-2"
          >
            <option value="">Route</option>
            {routes.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>

          <input
            type="date"
            value={newTrip.trip_date}
            onChange={(e) =>
              setNewTrip({ ...newTrip, trip_date: e.target.value })
            }
            className="border p-2"
          />

          <input
            type="time"
            value={newTrip.start_time}
            onChange={(e) =>
              setNewTrip({ ...newTrip, start_time: e.target.value })
            }
            className="border p-2"
          />

          <select
            value={newTrip.driver_id}
            onChange={(e) =>
              setNewTrip({ ...newTrip, driver_id: e.target.value })
            }
            className="border p-2"
          >
            <option value="">Driver</option>
            {drivers.map((d) => (
              <option key={d.user_id} value={d.user_id}>
                {d.name}
              </option>
            ))}
          </select>

          <select
            value={newTrip.bus_id}
            onChange={(e) =>
              setNewTrip({ ...newTrip, bus_id: e.target.value })
            }
            className="border p-2"
          >
            <option value="">Bus</option>
            {buses.map((b) => (
              <option key={b.id} value={b.id}>
                {b.code}
              </option>
            ))}
          </select>

        </div>

        <button
          onClick={createTrip}
          className="mt-4 bg-purple-600 text-white px-4 py-2"
        >
          Create Trip
        </button>
      </div>

      {/* FILTERS */}
      <div className="bg-white p-4 shadow rounded flex gap-4">
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

        <button
          onClick={fetchSchedule}
          className="bg-blue-600 text-white px-4"
        >
          Load
        </button>
      </div>

      {/* TABLE */}
      <div className="bg-white p-6 shadow rounded">
        <table className="w-full border text-center">
          <thead className="bg-gray-100">
            <tr>
              <th>Time</th>
              <th>Route</th>
              <th>Driver</th>
              <th>Bus</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {schedule.map((t) => (
              <tr key={t.id} className="border-t">
                <td>{t.start_time}</td>
                <td>{t.route_name}</td>
                <td>{t.driver_name}</td>
                <td>{t.bus_code}</td>
                <td>{t.status}</td>

                <td>
                  <button
                    onClick={() => setSelectedTrip(t)}
                    className="bg-yellow-500 text-white px-2"
                  >
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* EDIT */}
      {selectedTrip && (
        <div className="bg-white p-6 shadow rounded">
          <h2 className="font-semibold mb-4">Edit Trip</h2>

          <div className="grid grid-cols-2 gap-4">

            <input
              type="time"
              value={selectedTrip.start_time}
              onChange={(e) =>
                setSelectedTrip({
                  ...selectedTrip,
                  start_time: e.target.value,
                })
              }
              className="border p-2"
            />

            <select
              value={selectedTrip.driver_id}
              onChange={(e) =>
                setSelectedTrip({
                  ...selectedTrip,
                  driver_id: e.target.value,
                })
              }
              className="border p-2"
            >
              {drivers.map((d) => (
                <option key={d.user_id} value={d.user_id}>
                  {d.name}
                </option>
              ))}
            </select>

            <select
              value={selectedTrip.bus_id}
              onChange={(e) =>
                setSelectedTrip({
                  ...selectedTrip,
                  bus_id: e.target.value,
                })
              }
              className="border p-2"
            >
              {buses.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.code}
                </option>
              ))}
            </select>

          </div>

          <button
            onClick={updateTrip}
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

export default ScheduleManagement;