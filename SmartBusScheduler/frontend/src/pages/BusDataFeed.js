import React, { useEffect, useState } from "react";

function BusesDataFeed() {
  const [buses, setBuses] = useState([]);
  const [selectedBus, setSelectedBus] = useState(null);
  const [search, setSearch] = useState("");

  const [newBus, setNewBus] = useState({
    code: "",
    sitting_capacity: "",
    standing_capacity: "",
    status: "active",
  });

  const [message, setMessage] = useState("");

  // -------------------------
  // FETCH BUSES
  // -------------------------
  const fetchBuses = async () => {
    try {
      const res = await fetch("http://localhost:8000/admin/buses", {
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
        },
      });

      const data = await res.json();
      setBuses(data);

      /*
      RESPONSE:
      [
        {
          id: 1,
          code: "BUS101",
          sitting_capacity: 40,
          standing_capacity: 20,
          status: "active"
        }
      ]
      */
    } catch {
      setMessage("Failed to fetch buses");
    }
  };

  useEffect(() => {
    fetchBuses();
  }, []);

  // -------------------------
  // ADD BUS
  // -------------------------
  const addBus = async () => {
    if (!newBus.code || !newBus.sitting_capacity) {
      return setMessage("Code and sitting capacity required");
    }

    try {
      await fetch("http://localhost:8000/admin/buses", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
        },
        body: JSON.stringify(newBus),

        /*
        REQUEST:
        {
          code: "BUS101",
          sitting_capacity: 40,
          standing_capacity: 20,
          status: "active"
        }
        */
      });

      setMessage("Bus added!");
      setNewBus({
        code: "",
        sitting_capacity: "",
        standing_capacity: "",
        status: "active",
      });

      fetchBuses();
    } catch {
      setMessage("Failed to add bus");
    }
  };

  // -------------------------
  // UPDATE BUS
  // -------------------------
  const updateBus = async () => {
    try {
      await fetch(
        `http://localhost:8000/admin/buses/${selectedBus.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
          body: JSON.stringify(selectedBus),
        }
      );

      setMessage("Updated!");
      setSelectedBus(null);
      fetchBuses();
    } catch {
      setMessage("Update failed");
    }
  };

  // -------------------------
  // TOGGLE STATUS
  // -------------------------
  const toggleStatus = async (bus) => {
    const updated = {
      ...bus,
      status:
        bus.status === "active"
          ? "maintenance"
          : bus.status === "maintenance"
          ? "inactive"
          : "active",
    };

    try {
      await fetch(
        `http://localhost:8000/admin/buses/${bus.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
          body: JSON.stringify(updated),
        }
      );

      fetchBuses();
    } catch {
      setMessage("Status update failed");
    }
  };

  // -------------------------
  // FILTER
  // -------------------------
  const filteredBuses = buses.filter((b) =>
    b.code.toLowerCase().includes(search.toLowerCase())
  );

  // -------------------------
  // UI
  // -------------------------
  return (
    <div className="p-6 space-y-8">

      <h1 className="text-2xl font-bold">Buses Management</h1>

      {/* ADD BUS */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">Add Bus</h2>

        <div className="grid grid-cols-2 gap-4">

          <input
            placeholder="Bus Code"
            value={newBus.code}
            onChange={(e) =>
              setNewBus({ ...newBus, code: e.target.value })
            }
            className="border p-2"
          />

          <select
            value={newBus.status}
            onChange={(e) =>
              setNewBus({ ...newBus, status: e.target.value })
            }
            className="border p-2"
          >
            <option value="active">Active</option>
            <option value="maintenance">Maintenance</option>
            <option value="inactive">Inactive</option>
          </select>

          <input
            type="number"
            placeholder="Sitting Capacity"
            value={newBus.sitting_capacity}
            onChange={(e) =>
              setNewBus({
                ...newBus,
                sitting_capacity: e.target.value,
              })
            }
            className="border p-2"
          />

          <input
            type="number"
            placeholder="Standing Capacity"
            value={newBus.standing_capacity}
            onChange={(e) =>
              setNewBus({
                ...newBus,
                standing_capacity: e.target.value,
              })
            }
            className="border p-2"
          />
        </div>

        <button
          onClick={addBus}
          className="mt-4 bg-purple-600 text-white px-4 py-2"
        >
          Add Bus
        </button>
      </div>

      {/* TABLE */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">All Buses</h2>

        <input
          placeholder="Search by code..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border p-2 mb-4 w-full"
        />

        <table className="w-full border text-center">
          <thead className="bg-gray-100">
            <tr>
              <th>Code</th>
              <th>Sitting</th>
              <th>Standing</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {filteredBuses.map((b) => (
              <tr key={b.id} className="border-t">
                <td>{b.code}</td>
                <td>{b.sitting_capacity}</td>
                <td>{b.standing_capacity}</td>
                <td>{b.status}</td>

                <td className="space-x-2">
                  <button
                    onClick={() => setSelectedBus(b)}
                    className="bg-yellow-500 text-white px-2 py-1"
                  >
                    Edit
                  </button>

                  <button
                    onClick={() => toggleStatus(b)}
                    className="bg-blue-600 text-white px-2 py-1"
                  >
                    Toggle
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* EDIT */}
      {selectedBus && (
        <div className="bg-white p-6 shadow rounded">
          <h2 className="font-semibold mb-4">Edit Bus</h2>

          <div className="grid grid-cols-2 gap-4">

            <input
              value={selectedBus.code}
              onChange={(e) =>
                setSelectedBus({ ...selectedBus, code: e.target.value })
              }
              className="border p-2"
            />

            <select
              value={selectedBus.status}
              onChange={(e) =>
                setSelectedBus({ ...selectedBus, status: e.target.value })
              }
              className="border p-2"
            >
              <option value="active">Active</option>
              <option value="maintenance">Maintenance</option>
              <option value="inactive">Inactive</option>
            </select>

            <input
              type="number"
              value={selectedBus.sitting_capacity}
              onChange={(e) =>
                setSelectedBus({
                  ...selectedBus,
                  sitting_capacity: e.target.value,
                })
              }
              className="border p-2"
            />

            <input
              type="number"
              value={selectedBus.standing_capacity}
              onChange={(e) =>
                setSelectedBus({
                  ...selectedBus,
                  standing_capacity: e.target.value,
                })
              }
              className="border p-2"
            />
          </div>

          <button
            onClick={updateBus}
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

export default BusesDataFeed;