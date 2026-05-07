import React, { useState, useEffect, useRef } from "react";
import AdminLayout from "./AdminLayout";
import {
  Upload,
  Calendar,
  FileSpreadsheet,
  Settings,
  Download,
  Loader2,
} from "lucide-react";

const API_BASE =
  process.env.REACT_APP_API_BASE || "http://localhost:8000";

function ScheduleGeneration() {
  const token = sessionStorage.getItem("token");

  // ✅ refs instead of state (no re-render on typing)
  const templateNameRef = useRef();
  const busCountRef = useRef();
  const driverCountRef = useRef();
  const startDateRef = useRef();
  const endDateRef = useRef();
  const [file, setFile] = useState(null);
  const [overwrite, setOverwrite] = useState(false);
  const [preview, setPreview] = useState([]);

  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [templateDetails, setTemplateDetails] = useState([]);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const [summary, setSummary] = useState(null);
  const [logs, setLogs] = useState([]);

  /* =========================
     FETCH TEMPLATES
  ========================== */
  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await fetch(
        `${API_BASE}/admin/schedule/templates`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!res.ok) throw new Error();
      const data = await res.json();
      setTemplates(data);
    } catch {
      setMessage("Failed to load templates. Try to create some first.");
    }
  };

  const fetchTemplateDetails = async (templateId) => {
    if (!templateId) return;

    try {
      const res = await fetch(
        `${API_BASE}/admin/schedule/templates/${templateId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!res.ok) throw new Error();
      const data = await res.json();
      setTemplateDetails(data.records || []);
    } catch {
      setMessage("Failed to fetch template details.");
    }
  };

  /* =========================
     UI COMPONENTS
  ========================== */

  const Card = ({ title, icon: Icon, children }) => (
    <div className="bg-white shadow-md rounded-xl p-6 border border-gray-200">
      <div className="flex items-center gap-2 mb-4">
        {Icon && <Icon className="w-5 h-5 text-blue-600" />}
        <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
      </div>
      {children}
    </div>
  );

  const Button = ({
    children,
    onClick,
    variant = "primary",
    disabled = false,
    className = "",
  }) => {
    const styles = {
      primary: "bg-blue-600 hover:bg-blue-700 text-white",
      secondary: "bg-purple-600 hover:bg-purple-700 text-white",
      success: "bg-green-600 hover:bg-green-700 text-white",
      dark: "bg-gray-800 hover:bg-gray-900 text-white",
    };

    return (
      <button
        onClick={onClick}
        disabled={disabled}
        className={`px-4 py-2 rounded-lg transition flex items-center gap-2 ${
          disabled
            ? "bg-gray-400 cursor-not-allowed"
            : styles[variant]
        } ${className}`}
      >
        {disabled && <Loader2 className="w-4 h-4 animate-spin" />}
        {children}
      </button>
    );
  };

  /* =========================
     FILE HANDLING
  ========================== */

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

  const createTemplate = async () => {
    const name = templateNameRef.current.value;
    const bus_count = busCountRef.current.value;
    const driver_count = driverCountRef.current.value;

    if (!name || !bus_count || !driver_count) {
      setMessage("Fill all template fields.");
      return;
    }

    try {
      setLoading(true);
      setMessage("Creating template...");

      const res = await fetch(
        `${API_BASE}/admin/schedule/generate-templates`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            name,
            bus_count: Number(bus_count),
            driver_count: Number(driver_count),
          }),
        }
      );

      if (!res.ok) throw new Error();

      setMessage("Template created successfully.");

      // clear inputs
      templateNameRef.current.value = "";
      busCountRef.current.value = "";
      driverCountRef.current.value = "";

      fetchTemplates();
    } catch {
      setMessage("Template creation failed.");
    } finally {
      setLoading(false);
    }
  };

  const generateSchedule = async () => {
    const start_date = startDateRef.current.value;
    const end_date = endDateRef.current.value;

    if (!start_date || !end_date || !selectedTemplate) {
      setMessage("Select template and date range.");
      return;
    }

    try {
      setLoading(true);
      setMessage("Generating schedule...");

      const res = await fetch(
        `${API_BASE}/admin/schedule/generate-schedule`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            template_id: Number(selectedTemplate),
            start_date,
            end_date,
          }),
        }
      );

      if (!res.ok) throw new Error();

      const data = await res.json();
      setSummary(data.summary);
      setLogs(data.logs || []);
      setMessage("Schedule generated successfully.");
    } catch {
      setMessage("Schedule generation failed.");
    } finally {
      setLoading(false);
    }
  };

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

  /* =========================
     UI
  ========================== */

  return (
    <AdminLayout>
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          <h2 className="text-2xl font-bold">
            Smart Schedule Generation
          </h2>

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

          {/* STEP 2 */}
          <Card title="Create Template" icon={Settings}>
            <div className="flex flex-col gap-3 max-w-md">
              <input
                type="text"
                placeholder="Template Name"
                className="border p-2 rounded"
                ref={templateNameRef}
              />

              <input
                type="number"
                placeholder="Bus Count"
                className="border p-2 rounded"
                ref={busCountRef}
              />

              <input
                type="number"
                placeholder="Driver Count"
                className="border p-2 rounded"
                ref={driverCountRef}
              />

              <Button
                onClick={createTemplate}
                variant="secondary"
                disabled={loading}
              >
                Create Template
              </Button>
            </div>
          </Card>

          {/* STEP 3 */}
          <Card title="Generate Schedule" icon={Calendar}>
            <select
              className="border p-2 rounded mt-2"
              value={selectedTemplate}
              onChange={(e) => {
                setSelectedTemplate(e.target.value);
                fetchTemplateDetails(e.target.value);
              }}
            >
              <option value="">Select Template</option>
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>

            {templateDetails.length > 0 && (
              <table className="mt-4 border text-sm w-full">
                <thead>
                  <tr>
                    <th className="border p-2">Route</th>
                    <th className="border p-2">Start Time</th>
                  </tr>
                </thead>
                <tbody>
                  {templateDetails.map((rec, i) => (
                    <tr key={i}>
                      <td className="border p-2">{rec.route_id}</td>
                      <td className="border p-2">{rec.start_time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            <div className="mt-4 flex items-center gap-3">
              <input type="date" ref={startDateRef} />
              <input type="date" ref={endDateRef} />

              <Button
                onClick={generateSchedule}
                variant="success"
                disabled={loading}
              >
                Generate
              </Button>
            </div>
          </Card>

          {summary && (
            <div className="bg-white p-4 rounded shadow">
              Total Trips: {summary.total_trips}
            </div>
          )}

          {logs.length > 0 && (
            <Card title="Generated Trips" icon={FileSpreadsheet}>
              <Button onClick={downloadLogsCSV} variant="dark">
                <Download size={16} /> Download CSV
              </Button>

              <div className="overflow-auto max-h-[400px] mt-4">
                <table className="w-full border text-sm text-center">
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
            </Card>
          )}

          {message && (
            <div className="bg-blue-100 text-blue-800 p-3 rounded">
              {message}
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}

export default ScheduleGeneration;