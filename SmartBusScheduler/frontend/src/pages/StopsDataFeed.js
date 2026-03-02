import React, { useState, useRef } from "react";

function StopsDataFeed() {
  // -------------------------
  // States
  // -------------------------
  const [csvFile, setCsvFile] = useState(null);
  const [jsonInput, setJsonInput] = useState("");
  const [searchId, setSearchId] = useState("");
  const [stopData, setStopData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  // -------------------------
  // CSV Drag & Drop
  // -------------------------
  const fileInputRef = useRef(null);
  const [newStop, setNewStop] = useState({
    stop_code: "",
    stop_name: "",
    stop_lat: "",
    stop_lon: "",
  });
  // Add this function
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
      const res = await fetch("http://localhost:8000/admin/stops/upload-csv", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("CSV Upload failed");
      setMessage("CSV uploaded successfully!");
      setCsvFile(null);
    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // JSON Upload
  // -------------------------
  const uploadJSON = async () => {
    try {
      setLoading(true);

      const res = await fetch("http://localhost:8000/admin/stops/upload-json", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify([newStop]), // send as array
      });

      if (!res.ok) throw new Error("Upload failed");

      setMessage("Stop added successfully!");
      setNewStop({
        stop_code: "",
        stop_name: "",
        stop_lat: "",
        stop_lon: "",
      });
    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // Search Stop
  // -------------------------
const searchStop = async () => {
  if (!searchId) return;

  try {
    setLoading(true);

    const token = localStorage.getItem("token");

    const res = await fetch(
      `http://localhost:8000/admin/stops/${searchId}`,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      }
    );

    if (!res.ok) {
      if (res.status === 401) throw new Error("Unauthorized");
      if (res.status === 403) throw new Error("Admins only");
      if (res.status === 404) throw new Error("Stop not found");
    }

    const data = await res.json();
    setStopData(data);
    setMessage("");

  } catch (err) {
    setStopData(null);
    setMessage(err.message);
  } finally {
    setLoading(false);
  }
};

  // -------------------------
  // Update Stop
  // -------------------------
  const updateStop = async () => {
    try {
      const res = await fetch(
        `http://localhost:8000/admin/stops/${stopData.stop_id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(stopData),
        }
      );

      if (!res.ok) throw new Error("Update failed");
      setMessage("Stop updated successfully!");
    } catch (err) {
      setMessage(err.message);
    }
  };

  // -------------------------
  // Delete Stop
  // -------------------------
  const deleteStop = async () => {
    try {
      const res = await fetch(
        `http://localhost:8000/admin/stops/${stopData.stop_id}`,
        { method: "DELETE" }
      );

      if (!res.ok) throw new Error("Delete failed");

      setStopData(null);
      setMessage("Stop deleted successfully!");
    } catch (err) {
      setMessage(err.message);
    }
  };

  // -------------------------
  // UI
  // -------------------------
  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-bold">Stops Data Feed</h1>

      {/* TOP SECTION */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* CSV Upload */}
        <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-3">Upload Stops CSV</h2>

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

        {/* JSON Upload */}
        <div className="bg-white p-6 shadow rounded">
          <div className="mb-4">
            <h2 className="font-semibold mb-3">Add Stop</h2>

            <div className="grid grid-cols-2 gap-4">
              <input
                placeholder="Stop Code"
                value={newStop.stop_code}
                onChange={(e) =>
                  setNewStop({ ...newStop, stop_code: e.target.value })
                }
                className="border p-2 rounded"
              />

              <input
                placeholder="Stop Name"
                value={newStop.stop_name}
                onChange={(e) =>
                  setNewStop({ ...newStop, stop_name: e.target.value })
                }
                className="border p-2 rounded"
              />

              <input
                placeholder="Latitude"
                value={newStop.stop_lat}
                onChange={(e) =>
                  setNewStop({ ...newStop, stop_lat: e.target.value })
                }
                className="border p-2 rounded"
              />

              <input
                placeholder="Longitude"
                value={newStop.stop_lon}
                onChange={(e) =>
                  setNewStop({ ...newStop, stop_lon: e.target.value })
                }
                className="border p-2 rounded"
              />
            </div>

            <button
              onClick={uploadJSON}
              className="mt-4 bg-purple-600 text-white px-4 py-2 rounded"
              disabled={loading}
            >
              Add Stop
            </button>
          </div>
        </div>
      </div>

      {/* SEARCH + EDIT SECTION */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">Search Stop by ID</h2>

        <div className="flex gap-2 mb-4">
          <input
            type="number"
            placeholder="Enter stop_id"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
            className="border p-2 rounded w-48"
          />
          <button
            onClick={searchStop}
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            Search
          </button>
        </div>

        {stopData && (
          <table className="w-full border-collapse mb-4">
            <thead>
              <tr className="bg-purple-100">
                <th className="border p-2">Stop Code</th>
                <th className="border p-2">Stop Name</th>
                <th className="border p-2">Latitude</th>
                <th className="border p-2">Longitude</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border p-2">
                  <input
                    value={stopData.stop_code}
                    onChange={(e) =>
                      setStopData({ ...stopData, stop_code: e.target.value })
                    }
                  />
                </td>
                <td className="border p-2">
                  <input
                    value={stopData.stop_name}
                    onChange={(e) =>
                      setStopData({ ...stopData, stop_name: e.target.value })
                    }
                  />
                </td>
                <td className="border p-2">
                  <input
                    value={stopData.stop_lat}
                    onChange={(e) =>
                      setStopData({ ...stopData, stop_lat: e.target.value })
                    }
                  />
                </td>
                <td className="border p-2">
                  <input
                    value={stopData.stop_lon}
                    onChange={(e) =>
                      setStopData({ ...stopData, stop_lon: e.target.value })
                    }
                  />
                </td>
              </tr>
            </tbody>
          </table>
        )}

        {stopData && (
          <div className="flex gap-4">
            <button
              onClick={updateStop}
              className="bg-green-600 text-white px-4 py-2 rounded"
            >
              Update
            </button>

            <button
              onClick={deleteStop}
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

export default StopsDataFeed;