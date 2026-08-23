import React, { useRef, useState } from "react";

function SmartScheduleBuilder() {
  const fileRef = useRef(null);

  const [csvFile, setCsvFile] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [dateRange, setDateRange] = useState({
    start: "",
    end: "",
  });

  const [logs, setLogs] = useState("");
  const [loading, setLoading] = useState(false);

  // -------------------------
  // CSV UPLOAD
  // -------------------------
  const handleFile = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith(".csv")) {
      setCsvFile(file);
      setLogs("");
    } else {
      setLogs("Only CSV allowed");
    }
  };

  const uploadCSV = async () => {
    if (!csvFile) return setLogs("Select CSV first");

    const formData = new FormData();
    formData.append("file", csvFile);

    try {
      setLoading(true);

      await fetch("http://localhost:8000/admin/schedule/upload-demand-csv", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
        },
        body: formData,
      });

      setLogs("CSV uploaded successfully!");
    } catch {
      setLogs("Upload failed");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // GENERATE TEMPLATES
  // -------------------------
  const generateTemplates = async () => {
    try {
      setLoading(true);

      const res = await fetch(
        "http://localhost:8000/admin/schedule/generate-templates",
        {
          method: "POST",
        }
      );

      const data = await res.json();
      setTemplates(data);

      /*
      RESPONSE:
      [
        { type: "weekday", trips: [...] },
        { type: "weekend", trips: [...] }
      ]
      */

      setLogs("Templates generated!");
    } catch {
      setLogs("Generation failed");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // APPLY TEMPLATE
  // -------------------------
  const applyTemplate = async () => {
    if (!selectedTemplate || !dateRange.start || !dateRange.end) {
      return setLogs("Select template + date range");
    }

    try {
      setLoading(true);

      const res = await fetch(
        "http://localhost:8000/admin/schedule/apply-template",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
          body: JSON.stringify({
            template_type: selectedTemplate,
            start_date: dateRange.start,
            end_date: dateRange.end,
          }),
        }
      );

      const data = await res.json();

      /*
      RESPONSE:
      {
        trips_created: 120,
        conflicts: 5
      }
      */

      setLogs(
        `Created ${data.trips_created} trips, Conflicts: ${data.conflicts}`
      );
    } catch {
      setLogs("Apply failed");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // UI
  // -------------------------
  return (
    <div className="p-6 space-y-8">

      <h1 className="text-2xl font-bold">
        Smart Schedule Builder
      </h1>

      {/* CSV UPLOAD */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">Upload Demand CSV</h2>

        <input
          type="file"
          accept=".csv"
          ref={fileRef}
          onChange={handleFile}
          className="hidden"
        />

        <div
          onClick={() => fileRef.current.click()}
          className="border-2 border-dashed p-6 text-center cursor-pointer"
        >
          {csvFile ? csvFile.name : "Click to upload CSV"}
        </div>

        <button
          onClick={uploadCSV}
          className="mt-4 bg-purple-600 text-white px-4 py-2"
        >
          Upload
        </button>
      </div>

      {/* GENERATE */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">
          Generate Templates
        </h2>

        <button
          onClick={generateTemplates}
          className="bg-blue-600 text-white px-4 py-2"
        >
          Generate
        </button>
      </div>

      {/* TEMPLATE VIEW */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">
          Templates Preview
        </h2>

        <div className="space-y-4">
          {templates.map((t, i) => (
            <div key={i} className="border p-4 rounded">

              <h3 className="font-bold">{t.type}</h3>

              <p className="text-sm text-gray-500">
                Trips: {t.trips.length}
              </p>

              <button
                onClick={() => setSelectedTemplate(t.type)}
                className="mt-2 bg-green-600 text-white px-3 py-1"
              >
                Select
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* APPLY */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">
          Apply Template
        </h2>

        <select
          value={selectedTemplate}
          onChange={(e) => setSelectedTemplate(e.target.value)}
          className="border p-2 mr-2"
        >
          <option value="">Select Template</option>
          <option value="weekday">Weekday</option>
          <option value="weekend">Weekend</option>
          <option value="holiday">Holiday</option>
          <option value="semi-off">Semi-Off</option>
        </select>

        <input
          type="date"
          value={dateRange.start}
          onChange={(e) =>
            setDateRange({ ...dateRange, start: e.target.value })
          }
          className="border p-2 mr-2"
        />

        <input
          type="date"
          value={dateRange.end}
          onChange={(e) =>
            setDateRange({ ...dateRange, end: e.target.value })
          }
          className="border p-2 mr-2"
        />

        <button
          onClick={applyTemplate}
          className="bg-red-600 text-white px-4 py-2"
        >
          Generate Schedule
        </button>
      </div>

      {/* LOGS */}
      {logs && (
        <div className="bg-gray-100 p-4 rounded">
          <p>{logs}</p>
        </div>
      )}

    </div>
  );
}

export default SmartScheduleBuilder;