import React, { useState, useEffect } from "react";
import AdminLayout from "./AdminLayout";
import {
  Upload,
  Calendar,
  FileSpreadsheet,
  Settings,
  Download,
  Loader2,
} from "lucide-react";

function St() {
  const [file, setFile] = useState(null);
  const [overwrite, setOverwrite] = useState(false);
  const [preview, setPreview] = useState([]);

  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [templateDetails, setTemplateDetails] = useState([]);

  const [dateRange, setDateRange] = useState({
    start_date: "",
    end_date: "",
  });

  const [templateConfig, setTemplateConfig] = useState({
    name: "",
    bus_count: "",
    driver_count: "",
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [summary, setSummary] = useState(null);
  const [logs, setLogs] = useState([]);

  // =========================
  // STATIC DATA LOAD
  // =========================
  useEffect(() => {
    // simulate API load
    setTemplates([
      { id: 1, name: "Morning Plan", bus_count: 10, driver_count: 15 },
      { id: 2, name: "Evening Plan", bus_count: 8, driver_count: 12 },
    ]);
  }, []);

  // =========================
  // STATIC TEMPLATE DETAILS
  // =========================
  const fetchTemplateDetails = (id) => {
    if (!id) return;

    const mock = Array.from({ length: 5 }, (_, i) => ({
      route_id: `Route-${i + 1}`,
      start_time: `${8 + i}:00`,
    }));

    setTemplateDetails(mock);
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
        const rows = event.target.result
          .split("\n")
          .filter((r) => r.trim() !== "")
          .slice(0, 6);

        setPreview(rows.map((r) => r.split(",")));
      };
      reader.readAsText(f);
    }
  };

  // =========================
  // FAKE LOADER
  // =========================
  const simulate = (msg, cb) => {
    setLoading(true);
    setMessage(msg);

    setTimeout(() => {
      cb();
      setLoading(false);
    }, 800);
  };

  // =========================
  // UPLOAD CSV (STATIC)
  // =========================
  const uploadCSV = () => {
    if (!file) return setMessage("Please select a CSV file.");

    simulate("Uploading CSV...", () => {
      setMessage("CSV uploaded successfully.");
    });
  };

  // =========================
  // GENERATE TEMPLATE
  // =========================
  const generateTemplates = () => {
    simulate("Generating template...", () => {
      const newTemplate = {
        id: Date.now(),
        name: templateConfig.name || "Auto Template",
        bus_count: Number(templateConfig.bus_count) || 20,
        driver_count: Number(templateConfig.driver_count) || 30,
      };

      setTemplates((prev) => [...prev, newTemplate]);
      setMessage("Template generated successfully.");
    });
  };

  // =========================
  // GENERATE SCHEDULE
  // =========================
  const generateSchedule = () => {
    const { start_date, end_date } = dateRange;

    if (!start_date || !end_date || !selectedTemplate) {
      setMessage("Select template and date range.");
      return;
    }

    simulate("Generating schedule...", () => {
      const mockLogs = Array.from({ length: 12 }, (_, i) => ({
        trip_date: start_date,
        start_time: "08:00",
        route_name: `Route ${i + 1}`,
        driver_name: `Driver ${i + 1}`,
        bus_code: `BUS${i + 1}`,
        status: "Scheduled",
      }));

      setLogs(mockLogs);
      setSummary({
        total_trips: mockLogs.length,
        start_date,
        end_date,
      });

      setMessage("Schedule generated.");
    });
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

    const blob = new Blob([csvRows.join("\n")]);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "schedule.csv";
    a.click();
  };

  // =========================
  // UI COMPONENTS
  // =========================
  const Card = ({ title, icon: Icon, children }) => (
    <div className="bg-white shadow-md rounded-xl p-6 border">
      <div className="flex items-center gap-2 mb-4">
        {Icon && <Icon className="w-5 h-5 text-blue-600" />}
        <h2 className="text-lg font-semibold">{title}</h2>
      </div>
      {children}
    </div>
  );

  const Button = ({
    children,
    onClick,
    variant = "primary",
    disabled = false,
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
        className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
          disabled ? "bg-gray-400" : styles[variant]
        }`}
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

        {/* STEP 1 */}
        <Card title="Upload Observation CSV" icon={Upload}>
          <input type="file" onChange={handleFileChange} />
          <label className="flex gap-2 text-sm">
            <input
              type="checkbox"
              checked={overwrite}
              onChange={(e) => setOverwrite(e.target.checked)}
            />
            Overwrite existing
          </label>

          <Button onClick={uploadCSV} disabled={loading}>
            Upload CSV
          </Button>

          {preview.length > 0 && (
            <table className="w-full border text-sm mt-2">
              <tbody>
                {preview.map((row, i) => (
                  <tr key={i}>
                    {row.map((c, j) => (
                      <td key={j} className="border px-2 py-1">
                        {c}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        {/* STEP 2 */}
        <Card title="Generate Templates" icon={Settings}>
          <input
            placeholder="Name"
            onChange={(e) =>
              setTemplateConfig({ ...templateConfig, name: e.target.value })
            }
          />
          <input
            type="number"
            placeholder="Bus"
            onChange={(e) =>
              setTemplateConfig({ ...templateConfig, bus_count: e.target.value })
            }
          />
          <input
            type="number"
            placeholder="Driver"
            onChange={(e) =>
              setTemplateConfig({
                ...templateConfig,
                driver_count: e.target.value,
              })
            }
          />

          <Button onClick={generateTemplates} disabled={loading}>
            Generate Template
          </Button>
        </Card>

        {/* STEP 3 */}
        <Card title="Select Date Range" icon={Calendar}>
          <select
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
            <table className="w-full border text-sm mt-2">
              <tbody>
                {templateDetails.map((t, i) => (
                  <tr key={i}>
                    <td className="border p-1">{t.route_id}</td>
                    <td className="border p-1">{t.start_time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <input
            type="date"
            onChange={(e) =>
              setDateRange({ ...dateRange, start_date: e.target.value })
            }
          />
          <input
            type="date"
            onChange={(e) =>
              setDateRange({ ...dateRange, end_date: e.target.value })
            }
          />

          <Button onClick={generateSchedule} disabled={loading}>
            Generate Schedule
          </Button>
        </Card>

        {/* SUMMARY */}
        {summary && (
          <div className="grid grid-cols-3 gap-4">
            <div>Total: {summary.total_trips}</div>
            <div>Start: {summary.start_date}</div>
            <div>End: {summary.end_date}</div>
          </div>
        )}

        {/* TABLE */}
        {logs.length > 0 && (
          <Card title="Generated Trips" icon={FileSpreadsheet}>
            <Button onClick={downloadLogsCSV}>Download CSV</Button>

            <table className="w-full border text-sm mt-2">
              <tbody>
                {logs.map((l, i) => (
                  <tr key={i}>
                    <td>{l.trip_date}</td>
                    <td>{l.start_time}</td>
                    <td>{l.route_name}</td>
                    <td>{l.driver_name}</td>
                    <td>{l.bus_code}</td>
                    <td>{l.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}

        {message && <div className="bg-blue-100 p-2">{message}</div>}
      </div>
    </AdminLayout>
  );
}

export default St;