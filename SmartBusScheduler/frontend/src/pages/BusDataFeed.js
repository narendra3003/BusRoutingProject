import React, { useEffect, useState } from "react";
import AdminLayout from "./AdminLayout";

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
    <AdminLayout>
    <div className="p-6 space-y-8">

      <h1 className="text-2xl font-bold">Buses Management</h1>

      {/* ADD BUS */}
      <div className="bg-white p-6 rounded-xl shadow-md">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Add Bus
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        <input
          placeholder="Bus Code"
          value={newBus.code}
          onChange={(e) =>
            setNewBus({ ...newBus, code: e.target.value })
          }
          className="input"
        />

        <select
          value={newBus.status}
          onChange={(e) =>
            setNewBus({ ...newBus, status: e.target.value })
          }
          className="input"
        >
          <option value="active">Active</option>
          <option value="maintenance">Maintenance</option>
          <option value="inactive">Inactive</option>
        </select>

        <input
          type="number"
          placeholder="Seating Capacity"
          value={newBus.sitting_capacity}
          onChange={(e) =>
            setNewBus({
              ...newBus,
              sitting_capacity: e.target.value,
            })
          }
          className="input"
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
          className="input"
        />
      </div>

      <button
        onClick={addBus}
        className="mt-5 w-full py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
      >
        + Add Bus
      </button>
    </div>

      {/* TABLE */}
      <div className="bg-white p-6 rounded-xl shadow-md">

        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          All Buses
        </h2>

        <input
          placeholder="Search by code..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-3 py-2 border rounded-lg text-sm mb-4 focus:ring-2 focus:ring-purple-500 outline-none"
        />

        <table className="w-full text-sm text-gray-700">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">Code</th>
              <th className="px-4 py-3">Seating</th>
              <th className="px-4 py-3">Standing</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-center">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y">
            {filteredBuses.map((b) => (
              <tr key={b.id} className="hover:bg-gray-50 transition">

                <td className="px-4 py-3 font-semibold text-gray-800">
                  {b.code}
                </td>

                <td className="px-4 py-3">{b.sitting_capacity}</td>
                <td className="px-4 py-3">{b.standing_capacity}</td>

                {/* STATUS BADGE */}
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      b.status === "active"
                        ? "bg-green-100 text-green-700"
                        : b.status === "maintenance"
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {b.status}
                  </span>
                </td>

                {/* ACTIONS */}
                <td className="px-4 py-3 flex justify-center gap-2">

                  <button
                    onClick={() => setSelectedBus(b)}
                    className="px-3 py-1 text-xs bg-yellow-400 text-white rounded hover:bg-yellow-500 transition"
                  >
                    Edit
                  </button>

                  <button
                    onClick={() => toggleStatus(b)}
                    className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                  >
                    Toggle
                  </button>
                </td>
              </tr>
            ))}

            {filteredBuses.length === 0 && (
              <tr>
                <td colSpan="5" className="text-center py-6 text-gray-400">
                  No buses found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* EDIT */}
      {selectedBus && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">

          {/* BACKDROP */}
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setSelectedBus(null)}
          ></div>

          {/* MODAL */}
          <div className="relative bg-white w-full max-w-lg rounded-xl shadow-lg p-6">

            <h2 className="text-lg font-semibold mb-4">
              Edit Bus
            </h2>

            <div className="grid grid-cols-2 gap-4">

              <input
                value={selectedBus.code}
                onChange={(e) =>
                  setSelectedBus({ ...selectedBus, code: e.target.value })
                }
                className="input"
              />

              <select
                value={selectedBus.status}
                onChange={(e) =>
                  setSelectedBus({ ...selectedBus, status: e.target.value })
                }
                className="input"
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
                className="input"
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
                className="input"
              />
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setSelectedBus(null)}
                className="px-4 py-2 border rounded-lg"
              >
                Cancel
              </button>

              <button
                onClick={() => {
                  updateBus();
                  setSelectedBus(null);
                }}
                className="px-5 py-2 bg-green-600 text-white rounded-lg"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </AdminLayout>
  );
}

export default BusesDataFeed;