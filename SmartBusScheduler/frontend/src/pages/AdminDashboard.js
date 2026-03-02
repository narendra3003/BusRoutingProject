import React, { useState, useRef } from "react";

function AdminDashboard() {
  const [files, setFiles] = useState({ observations_data: null });
  const [errors, setErrors] = useState([]);
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");
  const [excelLink, setExcelLink] = useState("");
  const fileInputRefs = useRef({});

  const REQUIRED_KEYS = Object.keys(files);

  // ------------------------------
  // File handling
  // ------------------------------
  const handleFileChange = (key, file) => {
    setSuccess("");
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setErrors([`${key} must be a .csv file`]);
      return;
    }

    setErrors([]);
    setFiles((prev) => ({ ...prev, [key]: file }));
  };

  const handleDrop = (e, key) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    handleFileChange(key, file);
  };

  // ------------------------------
  // Validation
  // ------------------------------
  const validateFiles = () => {
    const newErrors = [];

    REQUIRED_KEYS.forEach((key) => {
      if (!files[key]) {
        newErrors.push(`${key.replace("_", " ")} not selected`);
      }
    });

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  // ------------------------------
  // Backend call
  // ------------------------------
  // const handleUpload = async () => {
  //   if (!validateFiles()) return;

  //   setLoading(true);
  //   setErrors([]);
  //   setSchedule([]);
  //   setSuccess("");

  //   try {
  //     const formData = new FormData();
  //     formData.append("observations", files.observations_data);
  //     formData.append("pop_size", 30);
  //     formData.append("ngen", 40);

  //     const res = await fetch("http://localhost:8000/admin/optimize", {
  //       method: "POST",
  //       body: formData,
  //     });

  //     if (!res.ok) {
  //       const errorData = await res.json();
  //       throw new Error(errorData.detail || "Optimization failed");
  //     }

  //     const data = await res.json();
  //     setSchedule(data.preview || []);
  //     setSuccess("Optimization completed successfully 🎉");
  //   } catch (err) {
  //     setErrors([err.message]);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  const handleDownloadTest = async () => {
    if (!validateFiles()) return;

    setLoading(true);
    setErrors([]);
    setSchedule([]);
    setSuccess("");
    setExcelLink("");

    try {
      const formData = new FormData();
      formData.append("observations", files.observations_data);

      const res = await fetch("http://localhost:8000/admin/optimize-and-report", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || "Optimization failed");
      }

      const data = await res.json();

      setSchedule(data.preview || []);
      setSuccess("Report generated successfully!");
      setExcelLink(`http://localhost:8000${data.excel_download}`);
    } catch (err) {
      setErrors([err.message]);
    } finally {
      setLoading(false);
    }
  };

  // ------------------------------
  // UI
  // ------------------------------
  return (
    <div className="min-h-screen bg-gray-100 p-8 space-y-8">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">
          Admin Optimization Dashboard
        </h1>
        <p className="text-gray-500 mt-1">
          Upload dataset and generate optimized bus schedules
        </p>
      </div>

      {/* Quick Links */}
      <div className="flex gap-4">
        <a href="/stops-data-feed" className="text-purple-600 hover:underline">
          Stops Data Feed
        </a>
        <a href="/routes-data-feed" className="text-purple-600 hover:underline">
          Routes Data Feed
        </a>
        <a href="/buses-data-feed" className="text-purple-600 hover:underline">
          Buses Data Feed
        </a>
      </div>

      {/* Upload Card */}
      <div className="bg-white rounded-xl shadow-md p-6 space-y-6">

        <h2 className="text-xl font-semibold text-gray-700">
          Upload Required Dataset
        </h2>

        {REQUIRED_KEYS.map((key) => (
          <div
            key={key}
            onDrop={(e) => handleDrop(e, key)}
            onDragOver={(e) => e.preventDefault()}
            className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-purple-400 transition"
            onClick={() => fileInputRefs.current[key].click()}
          >
            <input
              type="file"
              accept=".csv"
              ref={(el) => (fileInputRefs.current[key] = el)}
              hidden
              onChange={(e) =>
                handleFileChange(key, e.target.files[0])
              }
            />

            {!files[key] ? (
              <p className="text-gray-500">
                Drag & Drop or Click to Upload{" "}
                <span className="font-semibold">
                  {key.replace("_", " ")}
                </span>
              </p>
            ) : (
              <div className="flex justify-center items-center gap-2">
                <span className="text-green-600 font-medium">
                  {files[key].name}
                </span>
                <span className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded">
                  Selected
                </span>
              </div>
            )}
          </div>
        ))}


        {/* Errors */}
        {errors.length > 0 && (
          <div className="bg-red-100 text-red-700 p-3 rounded">
            {errors.map((err, idx) => <p key={idx}>{err}</p>)}
          </div>
        )}

        {/* Success */}
        {success && (
          <div className="bg-green-100 text-green-700 p-3 rounded">{success}</div>
        )}

        {/* Buttons */}
        <div className="flex gap-4">
          <button
            onClick={handleDownloadTest}
            disabled={loading}
            className="flex-1 bg-purple-600 text-white py-3 rounded-lg font-semibold hover:bg-purple-700 transition disabled:bg-gray-400 flex justify-center items-center"
          >
            {loading ? (
              <span className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
            ) : (
              "Validate & Download Report"
            )}
          </button>

          {excelLink && (
            <a
              href={excelLink}
              download
              className="flex-1 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 text-center"
            >
              Download Excel
            </a>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white rounded-xl shadow-md p-5">
          <h3 className="text-sm text-gray-500">Total Buses Scheduled</h3>
          <p className="text-2xl font-bold text-purple-600">
            {schedule.length > 0 ? schedule.length : "N/A"}
          </p>
        </div>
        <div className="bg-white rounded-xl shadow-md p-5">
          <h3 className="text-sm text-gray-500">Unique Drivers Assigned</h3>
          <p className="text-2xl font-bold text-purple-600">
            {new Set(schedule.map((row) => row.assigned_driver_id)).size || "N/A"}
          </p>
        </div>
        <div className="bg-white rounded-xl shadow-md p-5">
          <h3 className="text-sm text-gray-500">Unique Routes Covered</h3>
          <p className="text-2xl font-bold text-purple-600">
            {new Set(schedule.map((row) => row.route_id)).size || "N/A"}
          </p>
        </div>
        <div className="bg-white rounded-xl shadow-md p-5">
          <h3 className="text-sm text-gray-500">Optimization Status</h3>
          <p className={`text-2xl font-bold ${
            schedule.length > 0 ? "text-green-600" : "text-red-600"
          }`}>
            {schedule.length > 0 ? "Success" : "Pending"}
          </p>
        </div>
        {/* graphs */}
        
      </div>

      {/* Schedule Table */}
      {schedule.length > 0 && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">
            Optimized Schedule Preview
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-purple-100 text-left">
                  <th className="p-3">Bus ID</th>
                  <th className="p-3">Trip ID</th>
                  <th className="p-3">Route ID</th>
                  <th className="p-3">Planned Start</th>
                  <th className="p-3">Planned End</th>
                  <th className="p-3">Driver ID</th>
                </tr>
              </thead>
              <tbody>
                {schedule.map((row, idx) => (
                  <tr
                    key={idx}
                    className="border-b hover:bg-purple-50 transition"
                  >
                    <td className="p-3">{row.bus_id}</td>
                    <td className="p-3">{row.trip_id}</td>
                    <td className="p-3">{row.route_id}</td>
                    <td className="p-3">{row.planned_start}</td>
                    <td className="p-3">{row.planned_end}</td>
                    <td className="p-3">{row.assigned_driver_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;