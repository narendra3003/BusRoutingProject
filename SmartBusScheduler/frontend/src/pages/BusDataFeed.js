import React, { useState, useRef } from "react";

function BusDataFeed() {
  // -------------------------
  // States
  // -------------------------
  const [csvFile, setCsvFile] = useState(null);
  const [searchId, setSearchId] = useState("");
  const [busData, setBusData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const fileInputRef = useRef(null);

  const [newBus, setNewBus] = useState({
    bus_no: "",
    passenger_seats: "",
    passenger_cap: "",
  });

  // -------------------------
  // CSV Drag & Drop
  // -------------------------
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith(".csv")) {
      setCsvFile(file);
      setMessage("");
    } else {
      setMessage("Only CSV files allowed.");
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith(".csv")) {
      setCsvFile(file);
      setMessage("");
    } else {
      setMessage("Only CSV files allowed.");
    }
  };

  const handleDragOver = (e) => e.preventDefault();

  const uploadCSV = async () => {
    if (!csvFile) return setMessage("Please select a CSV file");

    const formData = new FormData();
    formData.append("file", csvFile);

    try {
      setLoading(true);

      const res = await fetch("http://localhost:8000/admin/bus/upload-csv", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: formData,
      });

      if (!res.ok) throw new Error("CSV upload failed");

      setMessage("CSV uploaded successfully!");
      setCsvFile(null);

    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // Add Bus (Form)
  // -------------------------
  const addBus = async () => {
    try {
      setLoading(true);

      const res = await fetch("http://localhost:8000/admin/bus", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          ...newBus,
          passenger_seats: parseInt(newBus.passenger_seats),
          passenger_cap: parseInt(newBus.passenger_cap),
        }),
      });

      if (!res.ok) throw new Error("Add failed");

      setMessage("Bus added successfully!");
      setNewBus({
        bus_no: "",
        passenger_seats: "",
        passenger_cap: "",
      });

    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // Search Bus
  // -------------------------
  const searchBus = async () => {
    if (!searchId) return;

    try {
      setLoading(true);

      const res = await fetch(
        `http://localhost:8000/admin/bus/${searchId}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!res.ok) throw new Error("Bus not found");

      const data = await res.json();
      setBusData(data);
      setMessage("");

    } catch (err) {
      setBusData(null);
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // Update Bus
  // -------------------------
  const updateBus = async () => {
    try {
      const res = await fetch(
        `http://localhost:8000/admin/bus/${busData.bus_id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({
            ...busData,
            passenger_seats: parseInt(busData.passenger_seats),
            passenger_cap: parseInt(busData.passenger_cap),
          }),
        }
      );

      if (!res.ok) throw new Error("Update failed");

      setMessage("Bus updated successfully!");

    } catch (err) {
      setMessage(err.message);
    }
  };

  // -------------------------
  // Delete Bus
  // -------------------------
  const deleteBus = async () => {
    try {
      const res = await fetch(
        `http://localhost:8000/admin/bus/${busData.bus_id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!res.ok) throw new Error("Delete failed");

      setBusData(null);
      setMessage("Bus deleted successfully!");

    } catch (err) {
      setMessage(err.message);
    }
  };

  // -------------------------
  // UI
  // -------------------------
  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-bold">Bus Data Feed</h1>

      {/* TOP SECTION */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* CSV Upload */}
        <div className="bg-white p-6 shadow rounded">
          <h2 className="font-semibold mb-3">Upload Bus CSV</h2>

          <input
            type="file"
            accept=".csv"
            ref={fileInputRef}
            onChange={handleFileSelect}
            className="hidden"
          />

          <div
            onClick={() => fileInputRef.current.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="border-2 border-dashed border-purple-400 p-8 text-center rounded cursor-pointer"
          >
            {csvFile ? (
              <p className="text-green-600">{csvFile.name}</p>
            ) : (
              <p>Drag & Drop CSV file here or Click to Browse</p>
            )}
          </div>

          <button
            onClick={uploadCSV}
            className="mt-4 bg-purple-600 text-white px-4 py-2 rounded"
            disabled={loading}
          >
            Upload CSV
          </button>
        </div>

        {/* Add Bus Form */}
        <div className="bg-white p-6 shadow rounded">
          <h2 className="font-semibold mb-3">Add Bus</h2>

          <div className="grid grid-cols-2 gap-4">
            <input
              placeholder="Bus Number"
              value={newBus.bus_no}
              onChange={(e) =>
                setNewBus({ ...newBus, bus_no: e.target.value })
              }
              className="border p-2 rounded"
            />

            <input
              placeholder="Passenger Seats"
              value={newBus.passenger_seats}
              onChange={(e) =>
                setNewBus({ ...newBus, passenger_seats: e.target.value })
              }
              className="border p-2 rounded"
            />

            <input
              placeholder="Passenger Capacity"
              value={newBus.passenger_cap}
              onChange={(e) =>
                setNewBus({ ...newBus, passenger_cap: e.target.value })
              }
              className="border p-2 rounded"
            />
          </div>

          <button
            onClick={addBus}
            className="mt-4 bg-purple-600 text-white px-4 py-2 rounded"
            disabled={loading}
          >
            Add Bus
          </button>
        </div>
      </div>

      {/* SEARCH + EDIT SECTION */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">Search Bus by ID</h2>

        <div className="flex gap-2 mb-4">
          <input
            type="number"
            placeholder="Enter bus_id"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
            className="border p-2 rounded w-48"
          />
          <button
            onClick={searchBus}
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            Search
          </button>
        </div>

        {busData && (
          <table className="w-full border-collapse mb-4">
            <thead>
              <tr className="bg-purple-100">
                <th className="border p-2">Bus No</th>
                <th className="border p-2">Seats</th>
                <th className="border p-2">Capacity</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border p-2">
                  <input
                    value={busData.bus_no}
                    onChange={(e) =>
                      setBusData({ ...busData, bus_no: e.target.value })
                    }
                  />
                </td>
                <td className="border p-2">
                  <input
                    value={busData.passenger_seats}
                    onChange={(e) =>
                      setBusData({ ...busData, passenger_seats: e.target.value })
                    }
                  />
                </td>
                <td className="border p-2">
                  <input
                    value={busData.passenger_cap}
                    onChange={(e) =>
                      setBusData({ ...busData, passenger_cap: e.target.value })
                    }
                  />
                </td>
              </tr>
            </tbody>
          </table>
        )}

        {busData && (
          <div className="flex gap-4">
            <button
              onClick={updateBus}
              className="bg-green-600 text-white px-4 py-2 rounded"
            >
              Update
            </button>

            <button
              onClick={deleteBus}
              className="bg-red-600 text-white px-4 py-2 rounded"
            >
              Delete
            </button>
          </div>
        )}

        {message && (
          <p className="mt-4 text-sm text-purple-700">{message}</p>
        )}
      </div>
    </div>
  );
}

export default BusDataFeed;