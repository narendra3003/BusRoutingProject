import React, { useState, useEffect, useRef } from "react";

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
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-bold">Stops Management</h1>

      {/* TOP SECTION */}
      <div className="grid md:grid-cols-2 gap-6">

        {/* ADD STOP */}
        <div className="bg-white p-6 shadow rounded">
          <h2 className="font-semibold mb-4">Add Stop</h2>

          <div className="grid grid-cols-2 gap-4">
            <input
              placeholder="Name"
              value={newStop.name}
              onChange={(e) =>
                setNewStop({ ...newStop, name: e.target.value })
              }
              className="border p-2 rounded"
            />

            <input
              placeholder="Zone"
              value={newStop.zone}
              onChange={(e) =>
                setNewStop({ ...newStop, zone: e.target.value })
              }
              className="border p-2 rounded"
            />

            <input
              type="number"
              placeholder="Latitude"
              value={newStop.lat}
              onChange={(e) =>
                setNewStop({ ...newStop, lat: e.target.value })
              }
              className="border p-2 rounded"
            />

            <input
              type="number"
              placeholder="Longitude"
              value={newStop.lon}
              onChange={(e) =>
                setNewStop({ ...newStop, lon: e.target.value })
              }
              className="border p-2 rounded"
            />

            <select
              value={newStop.type}
              onChange={(e) =>
                setNewStop({ ...newStop, type: e.target.value })
              }
              className="border p-2 rounded col-span-2"
            >
              <option value="stop">Stop</option>
              <option value="terminal">Terminal</option>
              <option value="depot">Depot</option>
            </select>
          </div>

          <button
            onClick={addStop}
            className="mt-4 bg-purple-600 text-white px-4 py-2 rounded"
          >
            Add Stop
          </button>
        </div>

        {/* CSV */}
        <div className="bg-white p-6 shadow rounded">
          <h2 className="font-semibold mb-4">Upload CSV</h2>

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
            className="border-2 border-dashed p-8 text-center cursor-pointer"
          >
            {csvFile ? csvFile.name : "Click or Drag CSV"}
          </div>

          <button
            onClick={uploadCSV}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded"
          >
            Upload
          </button>
        </div>
      </div>

      {/* TABLE */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">All Stops</h2>

        <input
          placeholder="Search by name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border p-2 mb-4 w-full"
        />

        <table className="w-full border">
          <thead>
            <tr className="bg-gray-100">
              <th>ID</th>
              <th>Name</th>
              <th>Zone</th>
              <th>Lat</th>
              <th>Lon</th>
              <th>Type</th>
              <th>Active</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {filteredStops.map((s) => (
              <tr key={s.id} className="text-center border-t">
                <td>{s.id}</td>
                <td>{s.name}</td>
                <td>{s.zone}</td>
                <td>{s.lat}</td>
                <td>{s.lon}</td>
                <td>{s.type}</td>
                <td>{s.is_active === true ? "Yes" : "No"}</td>

                <td className="space-x-2">
                  <button
                    onClick={() => setSelectedStop(s)}
                    className="bg-yellow-500 text-white px-2 py-1"
                  >
                    Edit
                  </button>

                  <button
                    onClick={() => deleteStop(s.id)}
                    className="bg-red-600 text-white px-2 py-1"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* EDIT */}
      {selectedStop && (
        <div className="bg-white p-6 shadow rounded">
          <h2 className="font-semibold mb-4">Edit Stop</h2>

          <div className="grid grid-cols-2 gap-4">
            <input
              value={selectedStop.name}
              onChange={(e) =>
                setSelectedStop({ ...selectedStop, name: e.target.value })
              }
              className="border p-2"
            />

            <input
              value={selectedStop.zone || ""}
              onChange={(e) =>
                setSelectedStop({ ...selectedStop, zone: e.target.value })
              }
              className="border p-2"
            />

            <input
              value={selectedStop.lat}
              onChange={(e) =>
                setSelectedStop({ ...selectedStop, lat: e.target.value })
              }
              className="border p-2"
            />

            <input
              value={selectedStop.lon}
              onChange={(e) =>
                setSelectedStop({ ...selectedStop, lon: e.target.value })
              }
              className="border p-2"
            />
          </div>

          <button
            onClick={updateStop}
            className="mt-4 bg-green-600 text-white px-4 py-2"
          >
            Save
          </button>
        </div>
      )}

      {message && <p className="text-purple-600">{message}</p>}
    </div>
  );
}

export default StopsDataFeed;