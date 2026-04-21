import React, { useState } from "react";
import AdminLayout from "./AdminLayout";
function ScheduleGeneration() {
  const [file, setFile] = useState(null);
  const [overwrite, setOverwrite] = useState(false);
  const [preview, setPreview] = useState([]);
  const [templates, setTemplates] = useState([]);

  const [dateRange, setDateRange] = useState({
    start_date: "",
    end_date: "",
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [summary, setSummary] = useState(null);
  const [logs, setLogs] = useState([]);

  const token = sessionStorage.getItem("token");

  // =========================
  // FILE HANDLING
  // =========================

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    setFile(f);

    if (f) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target.result;
        const rows = text.split("\n").slice(0, 6);
        setPreview(rows.map((r) => r.split(",")));
      };
      reader.readAsText(f);
    }
  };

  // =========================
  // UPLOAD CSV
  // =========================

  const uploadCSV = async () => {
    if (!file) {
      setMessage("Please select a CSV file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setMessage("");

      const res = await fetch(
        `http://localhost:8000/admin/schedule/upload-observations?overwrite=${overwrite}`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        }
      );

      if (!res.ok) {
        throw new Error("API failed");
      }
      const data = await res.json();
      setMessage(data.message || "CSV uploaded successfully.");
    } catch {
      setMessage("CSV upload failed.");
    } finally {
      setLoading(false);
    }
  };

  // =========================
  // GENERATE TEMPLATES
  // =========================

  const generateTemplates = async () => {
    try {
      setLoading(true);
      setMessage("Generating templates...");

      const res = await fetch(
        "http://localhost:8000/admin/schedule/generate-templates",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!res.ok) {
        throw new Error("API failed");
      }
      const data = await res.json();
      setTemplates(data.templates || []);
      setMessage("Templates generated.");
    } catch {
      setMessage("Template generation failed.");
    } finally {
      setLoading(false);
    }
  };

  // =========================
  // GENERATE FINAL SCHEDULE
  // =========================

  const generateSchedule = async () => {
    const { start_date, end_date } = dateRange;

    if (!start_date || !end_date) {
      setMessage("Select valid date range.");
      return;
    }

    try {
      setLoading(true);
      setMessage("Generating schedule...");

      const res = await fetch(
        "http://localhost:8000/admin/schedule/generate-from-observations",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ start_date, end_date }),
        }
      );

      if (!res.ok) {
        throw new Error("API failed");  
      }
      const data = await res.json();
      setSummary(data.summary);
      setLogs(data.logs || []);
      setMessage("Schedule generated.");
    } catch {
      setMessage("Schedule generation failed.");
    } finally {
      setLoading(false);
    }
  };

  // =========================
  // DOWNLOAD CSV
  // =========================

  const downloadLogsCSV = () => {
    if (!logs.length) return;

    const headers = [
      "trip_date",
      "start_time",
      "route_name",
      "driver_name",
      "bus_code",
      "status",
    ];

    const csvRows = [
      headers.join(","),
      ...logs.map((log) =>
        headers.map((h) => log[h] ?? "").join(",")
      ),
    ];

    const blob = new Blob([csvRows.join("\n")], {
      type: "text/csv",
    });

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "schedule.csv";
    a.click();
  };

  return (
    <AdminLayout>
    <div className="p-6 space-y-8 bg-gray-100 min-h-screen">
      <h1 className="text-3xl font-bold">
        Smart Schedule Generation
      </h1>
{/* STEP 1: UPLOAD */}
<div className="bg-white p-6 rounded shadow">
  <h2 className="text-xl font-semibold mb-4">
    Step 1: Upload OB CSV
  </h2>

  <input type="file" accept=".csv" onChange={handleFileChange} />

  {/* ✅ NEW: Overwrite Toggle */}
  <div className="mt-3 flex items-center gap-2">
    <input
      type="checkbox"
      id="overwrite"
      checked={overwrite}
      onChange={(e) => setOverwrite(e.target.checked)}
    />
    <label htmlFor="overwrite" className="text-sm">
      Overwrite existing data
    </label>
  </div>

  <button
  onClick={() => {
    if (overwrite) {
      const confirmDelete = window.confirm(
        "This will DELETE all existing OB data. Continue?"
      );
      if (!confirmDelete) return;
    }
    uploadCSV();
  }}
    className="ml-4 mt-3 bg-blue-600 text-white px-4 py-2 rounded"
  >
    Upload
  </button>

  {/* ✅ Mode indicator */}
  <p className="text-sm mt-2 text-gray-600">
    Mode: {overwrite ? "Overwrite (delete old data)" : "Append"}
  </p>

  {preview.length > 0 && (
    <div className="mt-4 overflow-auto">
      <p className="font-semibold mb-2">Preview:</p>
      <table className="border">
        <tbody>
          {preview.map((row, i) => (
            <tr key={i}>
              {row.map((col, j) => (
                <td key={j} className="border px-2 py-1">
                  {col}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )}
</div>

      {/* STEP 2: TEMPLATE */}
      <div className="bg-white p-6 rounded shadow">
        <h2 className="text-xl font-semibold mb-4">
          Step 2: Generate Templates
        </h2>

        <button
          onClick={generateTemplates}
          className="bg-purple-600 text-white px-4 py-2 rounded"
        >
          Generate Templates
        </button>

        {templates.length > 0 && (
          <div className="mt-4">
            <h3 className="font-semibold mb-2">Templates</h3>
            <table className="w-full border text-center">
              <thead>
                <tr>
                  <th className="border p-2">Type</th>
                  <th className="border p-2">Route</th>
                  <th className="border p-2">Start Time</th>
                </tr>
              </thead>
              <tbody>
                {templates.map((t, i) => (
                  <tr key={i}>
                    <td className="border p-2">{t.template_type}</td>
                    <td className="border p-2">{t.route_id}</td>
                    <td className="border p-2">{t.start_time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* STEP 3: DATE RANGE */}
      <div className="bg-white p-6 rounded shadow">
        <h2 className="text-xl font-semibold mb-4">
          Step 3: Select Date Range
        </h2>

        <input
          type="date"
          onChange={(e) =>
            setDateRange({ ...dateRange, start_date: e.target.value })
          }
        />
        <input
          type="date"
          className="ml-4"
          onChange={(e) =>
            setDateRange({ ...dateRange, end_date: e.target.value })
          }
        />

        <button
          onClick={generateSchedule}
          className="ml-4 bg-green-600 text-white px-4 py-2 rounded"
        >
          Generate Schedule
        </button>
      </div>

      {/* SUMMARY */}
      {summary && (
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-semibold">Summary</h2>
          <p>Total Trips: {summary.total_trips}</p>
        </div>
      )}

      {/* LOGS */}
      {logs.length > 0 && (
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-xl font-semibold mb-4">
            Generated Trips
          </h2>

          <button
            onClick={downloadLogsCSV}
            className="mb-3 bg-gray-700 text-white px-3 py-1 rounded"
          >
            Download CSV
          </button>

          <div className="overflow-auto max-h-[400px]">
            <table className="w-full border text-center">
              <thead>
                <tr>
                  <th className="border p-2">Date</th>
                  <th className="border p-2">Time</th>
                  <th className="border p-2">Route</th>
                  <th className="border p-2">Driver</th>
                  <th className="border p-2">Bus</th>
                  <th className="border p-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log, i) => (
                  <tr key={i}>
                    <td className="border p-2">{log.trip_date}</td>
                    <td className="border p-2">{log.start_time}</td>
                    <td className="border p-2">{log.route_name}</td>
                    <td className="border p-2">{log.driver_name}</td>
                    <td className="border p-2">{log.bus_code}</td>
                    <td className="border p-2">{log.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MESSAGE */}
      {message && (
        <div className="bg-purple-100 text-purple-700 p-3 rounded">
          {message}
        </div>
      )}
    </div>
    </AdminLayout>
  );
}

export default ScheduleGeneration;