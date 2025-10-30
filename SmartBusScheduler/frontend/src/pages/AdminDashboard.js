import React, { useState } from "react";
import Calendar from "react-calendar";
import "react-calendar/dist/Calendar.css";

function AdminDashboard() {
  const [files, setFiles] = useState({
    stops_data: null,
    routes_data: null,
    routes_timeplan: null,
    buses_data: null,
    drivers_data: null,
    observations_data: null,
  });
  const [errors, setErrors] = useState([]);
  const [schedule, setSchedule] = useState([]);
  const [expandedBus, setExpandedBus] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [loading, setLoading] = useState(false);

  const REQUIRED_KEYS = Object.keys(files);

  // ------------------------------
  // File input handling
  // ------------------------------
  const handleFileChange = (key, file) => {
    setFiles((prev) => ({ ...prev, [key]: file }));
  };

  // ------------------------------
  // Validation
  // ------------------------------
  const validateFiles = () => {
    const newErrors = [];

    REQUIRED_KEYS.forEach((key) => {
      const file = files[key];
      if (!file) {
        newErrors.push(`${key} not selected`);
      } else if (!file.name.toLowerCase().endsWith(".csv")) {
        newErrors.push(`${key} must be a .csv file`);
      }
    });

    setErrors(newErrors);
    if (newErrors.length > 0) {
      alert("Please fix the errors before uploading!");
      return false;
    }
    return true;
  };

  // ------------------------------
  // Backend call
  // ------------------------------
  const handleUpload = async () => {
    if (!validateFiles()) return;

    setLoading(true);
    setErrors([]);
    setSchedule([]);

    try {
      const formData = new FormData();
      formData.append("stops", files.stops_data);
      formData.append("routes", files.routes_data);
      formData.append("routes_timeplan", files.routes_timeplan);
      formData.append("buses", files.buses_data);
      formData.append("drivers", files.drivers_data);
      formData.append("observations", files.observations_data);

      // Optional GA params
      formData.append("pop_size", 30);
      formData.append("ngen", 40);

      const res = await fetch("http://localhost:8000/admin/optimize", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Optimization failed");
      }

      const data = await res.json();

      alert("✅ Optimization completed successfully!");
      console.log("Server response:", data);

      // Display preview schedule from backend
      setSchedule(data.preview || []);
    } catch (err) {
      console.error(err);
      alert(`❌ Upload failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const toggleBus = (busNumber) => {
    setExpandedBus(expandedBus === busNumber ? null : busNumber);
  };

  // ------------------------------
  // UI rendering
  // ------------------------------
  return (
    <div className="p-6 space-y-8">
      {/* Dataset Uploader */}
      <div className="bg-white p-4 shadow rounded">
        <h2 className="text-xl font-bold mb-3">Upload Required Dataset Files</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {REQUIRED_KEYS.map((key) => (
            <div key={key} className="flex flex-col">
              <label className="font-semibold mb-1 capitalize">
                {key.replace("_", " ")}:
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => handleFileChange(key, e.target.files[0])}
              />
              {files[key] && (
                <span className="text-green-600 text-sm mt-1">
                  ✅ {files[key].name}
                </span>
              )}
            </div>
          ))}
        </div>

        {errors.length > 0 && (
          <ul className="mt-4 text-red-600 text-sm list-disc list-inside">
            {errors.map((err, idx) => (
              <li key={idx}>{err}</li>
            ))}
          </ul>
        )}

        <button
          onClick={handleUpload}
          className="mt-4 bg-purple-600 text-white px-4 py-2 rounded disabled:bg-gray-400"
          disabled={loading}
        >
          {loading ? "Uploading & Optimizing..." : "Validate & Upload"}
        </button>
      </div>

      {/* Schedule Viewer */}
      {schedule.length > 0 && (
        <div className="bg-white p-4 shadow rounded">
          <h2 className="text-xl font-bold mb-3">Optimized Schedule Preview</h2>
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-purple-100 text-left">
                <th className="p-2 border">Bus ID</th>
                <th className="p-2 border">Trip ID</th>
                <th className="p-2 border">Route ID</th>
                <th className="p-2 border">Planned Start</th>
                <th className="p-2 border">Planned End</th>
                <th className="p-2 border">Driver ID</th>
              </tr>
            </thead>
            <tbody>
              {schedule.map((row, idx) => (
                <tr key={idx} className="hover:bg-purple-50">
                  <td className="p-2 border">{row.bus_id}</td>
                  <td className="p-2 border">{row.trip_id}</td>
                  <td className="p-2 border">{row.route_id}</td>
                  <td className="p-2 border">{row.planned_start}</td>
                  <td className="p-2 border">{row.planned_end}</td>
                  <td className="p-2 border">{row.assigned_driver_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Calendar Section */}
      {schedule.length > 0 && (
        <div className="bg-white p-4 shadow rounded flex flex-col items-center">
          <h2 className="text-xl font-bold mb-3">Check Schedule by Date</h2>
          <Calendar
            onChange={setSelectedDate}
            value={selectedDate}
            className="mb-4"
          />
          <p className="text-gray-600">
            Showing schedule for:{" "}
            <span className="font-semibold">{selectedDate.toDateString()}</span>
          </p>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
