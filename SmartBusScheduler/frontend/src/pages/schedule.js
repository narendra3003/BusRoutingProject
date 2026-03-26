// ============================================================
// PAGE: Admin Schedule Management
// Role: Admin
// PURPOSE: Create/edit trips, assign crew, manage buses
// ============================================================

import React, { useState, useEffect } from "react";

function AdminScheduleManagement() {

  const [trips, setTrips] = useState([]);
  const [availableDrivers, setAvailableDrivers] = useState([]);
  const [availableConductors, setAvailableConductors] = useState([]);
  const [availableBuses, setAvailableBuses] = useState([]);
  const [filterDate, setFilterDate] = useState(
    new Date().toISOString().slice(0, 10)
  );

  const [showModal, setShowModal] = useState(false);
  const [editingTrip, setEditingTrip] = useState(null);

  const [formData, setFormData] = useState({
    route: "",
    bus: "",
    driverId: "",
    conductorId: "",
    departure: "",
    arrival: "",
    date: filterDate,
    status: "scheduled",
  });

  // ----------------------------------------------------------
  // Load Trips
  // ----------------------------------------------------------

  useEffect(() => {
    loadTrips();
  }, [filterDate]);

  const loadTrips = async () => {
    try {
      // Replace with API call
      const demoTrips = [
        {
          id: "T-001",
          route: "Route 12A",
          bus: "BUS-101",
          driver: "J. Mehta",
          conductor: "R. Patel",
          departure: "06:00",
          arrival: "08:30",
          status: "scheduled",
        },
      ];

      setTrips(demoTrips);
    } catch (err) {
      alert("Failed to load trips");
    }
  };

  // ----------------------------------------------------------
  // Load Drivers / Conductors / Buses
  // ----------------------------------------------------------

  const loadCrewAndBuses = async () => {
    try {
      setAvailableDrivers([
        { id: "D-01", name: "A. Khan" },
        { id: "D-02", name: "J. Mehta" },
      ]);

      setAvailableConductors([
        { id: "C-01", name: "P. Sharma" },
        { id: "C-02", name: "R. Patel" },
      ]);

      setAvailableBuses([
        { id: "BUS-101", number: "MH-01-BT-4521" },
        { id: "BUS-102", number: "MH-01-BT-8832" },
      ]);
    } catch (err) {
      console.log(err);
    }
  };

  // ----------------------------------------------------------
  // CRUD Operations
  // ----------------------------------------------------------

  const createTrip = () => {
    const newTrip = {
      id: `T-${Date.now()}`,
      ...formData,
    };

    setTrips([...trips, newTrip]);
    setShowModal(false);
  };

  const updateTrip = () => {
    const updated = trips.map((t) =>
      t.id === editingTrip.id ? { ...t, ...formData } : t
    );

    setTrips(updated);
    setShowModal(false);
    setEditingTrip(null);
  };

  const deleteTrip = (id) => {
    if (!window.confirm("Delete this trip?")) return;

    const filtered = trips.filter((t) => t.id !== id);
    setTrips(filtered);
  };

  // ----------------------------------------------------------
  // Modal
  // ----------------------------------------------------------

  const openCreateModal = async () => {
    await loadCrewAndBuses();

    setFormData({
      route: "",
      bus: "",
      driverId: "",
      conductorId: "",
      departure: "",
      arrival: "",
      date: filterDate,
      status: "scheduled",
    });

    setEditingTrip(null);
    setShowModal(true);
  };

  const openEditModal = async (trip) => {
    await loadCrewAndBuses();

    setEditingTrip(trip);
    setFormData(trip);
    setShowModal(true);
  };

  const handleSubmit = () => {
    if (editingTrip) updateTrip();
    else createTrip();
  };

  // ----------------------------------------------------------
  // UI
  // ----------------------------------------------------------

  return (
    <div className="min-h-screen bg-gray-100 p-6">

      {/* HEADER */}

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Schedule Management</h1>

        <button
          onClick={openCreateModal}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg"
        >
          + New Trip
        </button>
      </div>

      {/* DATE FILTER */}

      <div className="mb-6">
        <input
          type="date"
          value={filterDate}
          onChange={(e) => setFilterDate(e.target.value)}
          className="border p-2 rounded"
        />
      </div>

      {/* TABLE */}

      <div className="bg-white rounded-xl shadow overflow-x-auto">

        <table className="w-full text-left">

          <thead className="bg-gray-200">

            <tr>
              <th className="p-3">Trip ID</th>
              <th>Route</th>
              <th>Bus</th>
              <th>Driver</th>
              <th>Conductor</th>
              <th>Departure</th>
              <th>Arrival</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>

          </thead>

          <tbody>

            {trips.length === 0 ? (
              <tr>
                <td colSpan="9" className="text-center p-6">
                  No Trips
                </td>
              </tr>
            ) : (
              trips.map((trip) => (
                <tr key={trip.id} className="border-t">

                  <td className="p-3 font-semibold">{trip.id}</td>

                  <td>{trip.route}</td>

                  <td>{trip.bus}</td>

                  <td>{trip.driver}</td>

                  <td>{trip.conductor}</td>

                  <td>{trip.departure}</td>

                  <td>{trip.arrival}</td>

                  <td className="text-blue-600">{trip.status}</td>

                  <td className="space-x-2">

                    <button
                      onClick={() => openEditModal(trip)}
                      className="bg-yellow-500 text-white px-3 py-1 rounded"
                    >
                      Edit
                    </button>

                    <button
                      onClick={() => deleteTrip(trip.id)}
                      className="bg-red-600 text-white px-3 py-1 rounded"
                    >
                      Delete
                    </button>

                  </td>

                </tr>
              ))
            )}

          </tbody>

        </table>

      </div>

      {/* MODAL */}

      {showModal && (

        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center">

          <div className="bg-white p-6 rounded-xl w-96">

            <h2 className="text-xl font-bold mb-4">
              {editingTrip ? "Edit Trip" : "Create Trip"}
            </h2>

            <div className="space-y-3">

              <input
                placeholder="Route"
                value={formData.route}
                onChange={(e) =>
                  setFormData({ ...formData, route: e.target.value })
                }
                className="w-full border p-2 rounded"
              />

              <input
                type="time"
                value={formData.departure}
                onChange={(e) =>
                  setFormData({ ...formData, departure: e.target.value })
                }
                className="w-full border p-2 rounded"
              />

              <input
                type="time"
                value={formData.arrival}
                onChange={(e) =>
                  setFormData({ ...formData, arrival: e.target.value })
                }
                className="w-full border p-2 rounded"
              />

            </div>

            <div className="flex justify-end gap-3 mt-5">

              <button
                onClick={() => setShowModal(false)}
                className="bg-gray-400 text-white px-4 py-2 rounded"
              >
                Cancel
              </button>

              <button
                onClick={handleSubmit}
                className="bg-blue-600 text-white px-4 py-2 rounded"
              >
                {editingTrip ? "Update" : "Create"}
              </button>

            </div>

          </div>

        </div>

      )}
    </div>
  );
}

export default AdminScheduleManagement;