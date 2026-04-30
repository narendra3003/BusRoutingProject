import React, { useState, useEffect, useRef } from "react";
import AdminLayout from "./AdminLayout";
function StopsDataFeed() {
  // -------------------------
  // States
  // -------------------------
  const [csvFile, setCsvFile] = useState(null);
  const [search, setSearch] = useState("");
  const [stops, setStops] = useState([]);
  const [selectedStop, setSelectedStop] = useState(null);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const fileInputRef = useRef(null);

  const [newStop, setNewStop] = useState({
    name: "",
    lat: "",
    lon: "",
    zone: "",
    type: "stop",
  });

  // -------------------------
  // FETCH ALL STOPS
  // -------------------------
  const fetchStops = async () => {
    try {
      setLoading(true);
      const token = sessionStorage.getItem("token");

      const res = await fetch("http://localhost:8000/stops", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();
      setStops(data);
    } catch (err) {
      setMessage("Failed to fetch stops");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStops();
  }, []);

  // -------------------------
  // CSV Upload
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

  const uploadCSV = async () => {
    if (!csvFile) return setMessage("Select CSV first");

    const formData = new FormData();
    formData.append("file", csvFile);

    try {
      setLoading(true);
      const token = sessionStorage.getItem("token");

      const res = await fetch(
        "http://localhost:8000/admin/stops/upload",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      if (!res.ok) throw new Error();

      setMessage("CSV uploaded!");
      setCsvFile(null);
      fetchStops();
    } catch {
      setMessage("Upload failed");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // ADD STOP
  // -------------------------
  const addStop = async () => {
    if (!newStop.name || !newStop.lat || !newStop.lon) {
      return setMessage("Name, lat, lon required");
    }

    try {
      setLoading(true);
      const token = sessionStorage.getItem("token");

      await fetch("http://localhost:8000/admin/stops", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(newStop),
      });

      setMessage("Stop added!");
      setNewStop({
        name: "",
        lat: "",
        lon: "",
        zone: "",
        type: "stop",
      });

      fetchStops();
    } catch {
      setMessage("Failed to add stop");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // UPDATE STOP
  // -------------------------
  const updateStop = async () => {
    try {
      const token = sessionStorage.getItem("token");

      console.log("Updating stop:", selectedStop);

      await fetch(
        `http://localhost:8000/admin/stops/${selectedStop.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            name: selectedStop.name,
            lat: selectedStop.lat,
            lon: selectedStop.lon,
            type: selectedStop.type,
            zone: selectedStop.zone,
            is_active: selectedStop.is_active,
          })
        }
      );

      setMessage("Updated!");
      setSelectedStop(null);
      fetchStops();
    } catch {
      setMessage("Update failed");
    }
  };

  // -------------------------
  // DELETE STOP
  // -------------------------
  const deleteStop = async (id) => {
    try {
      const token = sessionStorage.getItem("token");

      await fetch(`http://localhost:8000/admin/stops/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setMessage("Deleted!");
      fetchStops();
    } catch {
      setMessage("Delete failed");
    }
  };

  // -------------------------
  // FILTERED STOPS
  // -------------------------
  const filteredStops = stops.filter((s) =>
    s.name.toLowerCase().includes(search.toLowerCase())
  );

  // -------------------------
  // UI
  // -------------------------
  return (
    <AdminLayout>
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-bold">Stops Management</h1>

      {/* TOP SECTION */}
      <div className="grid md:grid-cols-2 gap-6">

        {/* ADD STOP */}
        <div className="bg-white p-6 rounded-xl shadow-md">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Add Stop
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            <input
              placeholder="Name"
              value={newStop.name}
              onChange={(e) =>
                setNewStop({ ...newStop, name: e.target.value })
              }
              className="input"
            />

            <input
              placeholder="Zone"
              value={newStop.zone}
              onChange={(e) =>
                setNewStop({ ...newStop, zone: e.target.value })
              }
              className="input"
            />

            <input
              type="number"
              placeholder="Latitude"
              value={newStop.lat}
              onChange={(e) =>
                setNewStop({ ...newStop, lat: e.target.value })
              }
              className="input"
            />

            <input
              type="number"
              placeholder="Longitude"
              value={newStop.lon}
              onChange={(e) =>
                setNewStop({ ...newStop, lon: e.target.value })
              }
              className="input"
            />

            <select
              value={newStop.type}
              onChange={(e) =>
                setNewStop({ ...newStop, type: e.target.value })
              }
              className="input col-span-1 md:col-span-2"
            >
              <option value="stop">Stop</option>
              <option value="terminal">Terminal</option>
              <option value="depot">Depot</option>
            </select>
          </div>

          <button
            onClick={addStop}
            className="mt-5 w-full py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
          >
            + Add Stop
          </button>
        </div>

        {/* CSV */}
        <div className="bg-white p-6 rounded-xl shadow-md">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Upload CSV
          </h2>

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
            onDragOver={(e) => e.preventDefault()}
            className="border-2 border-dashed rounded-xl p-10 text-center cursor-pointer hover:bg-gray-50 transition"
          >
            <p className="text-sm text-gray-500">
              {csvFile ? csvFile.name : "Click or Drag CSV here"}
            </p>
          </div>

          <button
            onClick={uploadCSV}
            className="mt-5 w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Upload CSV
          </button>
        </div>
      </div>

      {/* TABLE */}
      <div className="bg-white p-6 rounded-xl shadow-md">

        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          All Stops
        </h2>

        <input
          placeholder="Search by name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-3 py-2 border rounded-lg text-sm mb-4 focus:ring-2 focus:ring-purple-500 outline-none"
        />

        <table className="w-full text-sm text-gray-700">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">ID</th>
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3">Zone</th>
              <th className="px-4 py-3">Lat</th>
              <th className="px-4 py-3">Lon</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-center">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y">
            {filteredStops.map((s) => (
              <tr key={s.id} className="hover:bg-gray-50 transition">

                <td className="px-4 py-3 font-medium">#{s.id}</td>

                <td className="px-4 py-3 font-semibold text-gray-800">
                  {s.name}
                </td>

                <td className="px-4 py-3">{s.zone}</td>
                <td className="px-4 py-3">{s.lat}</td>
                <td className="px-4 py-3">{s.lon}</td>

                {/* TYPE BADGE */}
                <td className="px-4 py-3">
                  <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-700">
                    {s.type}
                  </span>
                </td>

                {/* STATUS BADGE */}
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      s.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {s.is_active ? "Active" : "Inactive"}
                  </span>
                </td>

                {/* ACTIONS */}
                <td className="px-4 py-3 flex justify-center gap-2">
                  <button
                    onClick={() => setSelectedStop(s)}
                    className="px-3 py-1 text-xs bg-yellow-400 text-white rounded hover:bg-yellow-500 transition"
                  >
                    Edit
                  </button>

                  <button
                    onClick={() => deleteStop(s.id)}
                    className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}

            {filteredStops.length === 0 && (
              <tr>
                <td colSpan="8" className="text-center py-6 text-gray-400">
                  No stops found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {/* EDIT */}
      {selectedStop && (
  <div className="fixed inset-0 z-50 flex items-center justify-center">

    {/* BACKDROP */}
    <div
      className="absolute inset-0 bg-black/40 backdrop-blur-sm"
      onClick={() => setSelectedStop(null)}
    ></div>

    {/* MODAL */}
    <div className="relative bg-white w-full max-w-lg rounded-xl shadow-lg p-6">

      <h2 className="text-lg font-semibold mb-4">Edit Stop</h2>

      <div className="grid grid-cols-2 gap-4">

        <input
          value={selectedStop.name}
          onChange={(e) =>
            setSelectedStop({ ...selectedStop, name: e.target.value })
          }
          className="input"
        />

        <input
          value={selectedStop.zone || ""}
          onChange={(e) =>
            setSelectedStop({ ...selectedStop, zone: e.target.value })
          }
          className="input"
        />

        <input
          value={selectedStop.lat}
          onChange={(e) =>
            setSelectedStop({ ...selectedStop, lat: e.target.value })
          }
          className="input"
        />

        <input
          value={selectedStop.lon}
          onChange={(e) =>
            setSelectedStop({ ...selectedStop, lon: e.target.value })
          }
          className="input"
        />
      </div>

      <div className="mt-6 flex justify-end gap-3">
        <button
          onClick={() => setSelectedStop(null)}
          className="px-4 py-2 border rounded-lg"
        >
          Cancel
        </button>

        <button
          onClick={() => {
            updateStop();
            setSelectedStop(null);
          }}
          className="px-5 py-2 bg-green-600 text-white rounded-lg"
        >
          Save
        </button>
      </div>
    </div>
  </div>
)}

      {message && <p className="text-purple-600">{message}</p>}
    </div>
    </AdminLayout>
  );
}

export default StopsDataFeed;