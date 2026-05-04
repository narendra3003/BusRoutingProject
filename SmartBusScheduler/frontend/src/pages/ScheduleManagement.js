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

function ScheduleGeneration() {
  const [file, setFile] = useState(null);
  const [overwrite, setOverwrite] = useState(false);
  const [preview, setPreview] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [templateDetails, setTemplateDetails] = useState([]);

const startDateRef = useRef(null);
const endDateRef = useRef(null);

const templateNameRef = useRef(null);
const busCountRef = useRef(null);
const driverCountRef = useRef(null);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [summary, setSummary] = useState(null);
  const [logs, setLogs] = useState([]);

  const token = sessionStorage.getItem("token");

  // =========================
  // FETCH TEMPLATES ON LOAD
  // =========================
  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await fetch(
        "http://localhost:8000/admin/schedule/templates",
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!res.ok) throw new Error();
      const data = await res.json();
      setTemplates(data);
    } catch {
      setMessage("Failed to load templates.");
    }
  };

  const fetchTemplateDetails = async (id) => {
    if (!id) return;
    try {
      const res = await fetch(
        `http://localhost:8000/admin/schedule/templates/${id}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!res.ok) throw new Error();
      const data = await res.json();
      setTemplateDetails(data);
    } catch {
      setMessage("Failed to load template details.");
    }
  };

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
        const rows = text
          .split("\n")
          .filter((r) => r.trim() !== "")
          .slice(0, 6);

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

      if (!res.ok) throw new Error();

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
const payload = {
  name:
    templateNameRef.current.value.trim() || "Auto Template",

  bus_count:
    parseInt(busCountRef.current.value, 10) || 34,

  driver_count:
    parseInt(driverCountRef.current.value, 10) || 50,
};

console.log(payload);
      const res = await fetch(
        "http://localhost:8000/admin/schedule/generate-templates",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            payload,
          })
        }
      );

      if (!res.ok) throw new Error();

      setMessage("Template generated successfully.");

      // ✅ IMPORTANT: refresh template list
      fetchTemplates();
    } catch {
      setMessage("Template generation failed.");
    } finally {
      setLoading(false);
    }
  };

  // =========================
  // GENERATE SCHEDULE
  // =========================
  const generateSchedule = async () => {
    const { start_date, end_date } = {
      start_date: startDateRef.current.value,
      end_date: endDateRef.current.value,
    };

    if (!start_date || !end_date || !selectedTemplate) {
      setMessage("Select template and date range.");
      return;
    }

    try {
      setLoading(true);
      setMessage("Generating schedule...");

      const res = await fetch(
        "http://localhost:8000/admin/schedule/generate-schedule",
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

  return (
    <AdminLayout>
      <div className="p-6 space-y-8 bg-gray-100 min-h-screen">
        <h1 className="text-3xl font-bold">
          Smart Schedule Generation
        </h1>

        {/* STEP 1: Upload CSV */}
        <Card title="Upload Observation CSV" icon={Upload}>
          <div className="flex flex-col gap-4">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="border p-2 rounded-lg"
            />

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={overwrite}
                onChange={(e) => setOverwrite(e.target.checked)}
              />
              Overwrite existing data
            </label>

            <Button onClick={uploadCSV} disabled={loading}>
              <Upload size={16} /> Upload CSV
            </Button>

            {preview.length > 0 && (
              <div className="overflow-auto">
                <table className="w-full border text-sm">
                  <tbody>
                    {preview.map((row, i) => (
                      <tr key={i} className="odd:bg-gray-50">
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
        </Card>

        {/* STEP 2: Templates */}
        <Card title="Generate Templates" icon={Settings}>
          <div className="flex flex-col gap-4">
            <input
              type="text"
              placeholder="Template Name"
              className="border p-2 rounded-lg"
              ref={templateNameRef}
            />

<input
  type="number"
  placeholder="Bus Count"
  className="border p-2 rounded-lg"
  defaultValue={34}
  ref={busCountRef}
/>

<input
  type="number"
  placeholder="Driver Count"
  className="border p-2 rounded-lg"
  defaultValue={50}
  ref={driverCountRef}
/>
            <Button
              onClick={generateTemplates}
              variant="secondary"
              disabled={loading}
            >
              Generate Template
            </Button>
          </div>
        </Card>

        {/* STEP 3: Date Range */}
        <Card title="Select Date Range" icon={Calendar}>
          <div className="flex flex-wrap gap-4 items-center">
            <select
              className="border p-2 rounded-lg"
              value={selectedTemplate}
              onChange={(e) => {
                const id = e.target.value;
                setSelectedTemplate(id);
                fetchTemplateDetails(id);
              }}
            >
              <option value="">Select Template</option>
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} | Buses: {t.bus_count} | Drivers:{" "}
                  {t.driver_count}
                </option>
              ))}
            </select>

            {templateDetails.length > 0 && (
              <div className="overflow-auto max-h-[250px]">
                <table className="w-full border text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border p-2">Route</th>
                      <th className="border p-2">Start Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {templateDetails.map((rec, i) => (
                      <tr key={i}>
                        <td className="border p-2">
                          {rec.route_id}
                        </td>
                        <td className="border p-2">
                          {rec.start_time}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
<input
  type="date"
  className="border p-2 rounded-lg"
  ref={startDateRef}
/>

<input
  type="date"
  className="border p-2 rounded-lg"
  ref={endDateRef}
/>
            <Button
              onClick={generateSchedule}
              variant="success"
              disabled={loading}
            >
              Generate Schedule
            </Button>
          </div>
        </Card>

        {/* SUMMARY */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: "Total Trips", value: summary.total_trips },
              { label: "Start Date", value: summary.start_date },
              { label: "End Date", value: summary.end_date },
            ].map((item, i) => (
              <div
                key={i}
                className="bg-white p-4 rounded-xl shadow border"
              >
                <p className="text-gray-500 text-sm">
                  {item.label}
                </p>
                <p className="text-2xl font-bold">
                  {item.value}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* SCHEDULE TABLE */}
        {logs.length > 0 && (
          <Card title="Generated Trips" icon={FileSpreadsheet}>
            <Button
              onClick={downloadLogsCSV}
              variant="dark"
              className="mb-4"
            >
              <Download size={16} /> Download CSV
            </Button>

            <div className="overflow-auto max-h-[400px]">
              <table className="w-full border text-center text-sm">
                <thead className="bg-gray-100 sticky top-0">
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
                    <tr key={i} className="odd:bg-gray-50">
                      <td className="border p-2">
                        {log.trip_date}
                      </td>
                      <td className="border p-2">
                        {log.start_time}
                      </td>
                      <td className="border p-2">
                        {log.route_name}
                      </td>
                      <td className="border p-2">
                        {log.driver_name}
                      </td>
                      <td className="border p-2">
                        {log.bus_code}
                      </td>
                      <td className="border p-2">
                        {log.status}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* MESSAGE */}
        {message && (
          <div className="bg-blue-100 text-blue-800 p-3 rounded-lg shadow">
            {message}
          </div>
        )}
      </div>
    </AdminLayout>
  );
}

export default ScheduleGeneration;