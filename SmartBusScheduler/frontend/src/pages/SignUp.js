import React, { useState } from "react";
import API from "../api/api";

function UploaderDashboard() {
  const [data, setData] = useState({ bus_no: "", route_id: "", stop_id: "", boarding_count: "", alighting_count: "", timestamp: "" });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setData({ ...data, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    API.post("/uploader/observations/upload", data)
      .then((res) => setMessage(res.data.message))
      .catch((err) => setMessage("Error uploading data."))
      .finally(() => setLoading(false));
  };

  return (
    <div className="max-w-lg mx-auto mt-8 bg-white rounded-xl shadow p-8">
      <h2 className="text-2xl font-bold mb-6 text-purple-700 flex items-center gap-2">📤 Upload Observation</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block font-semibold mb-1">Bus No</label>
          <input name="bus_no" value={data.bus_no} onChange={handleChange} className="border p-2 rounded w-full" required />
        </div>
        <div>
          <label className="block font-semibold mb-1">Route ID</label>
          <input name="route_id" value={data.route_id} onChange={handleChange} className="border p-2 rounded w-full" required />
        </div>
        <div>
          <label className="block font-semibold mb-1">Stop ID</label>
          <input name="stop_id" value={data.stop_id} onChange={handleChange} className="border p-2 rounded w-full" required />
        </div>
        <div>
          <label className="block font-semibold mb-1">Boarding Count</label>
          <input name="boarding_count" value={data.boarding_count} onChange={handleChange} className="border p-2 rounded w-full" required />
        </div>
        <div>
          <label className="block font-semibold mb-1">Alighting Count</label>
          <input name="alighting_count" value={data.alighting_count} onChange={handleChange} className="border p-2 rounded w-full" required />
        </div>
        <div>
          <label className="block font-semibold mb-1">Timestamp</label>
          <input name="timestamp" value={data.timestamp} onChange={handleChange} className="border p-2 rounded w-full" required />
        </div>
        <button type="submit" className="bg-purple-600 text-white px-6 py-2 rounded hover:bg-purple-700 transition w-full" disabled={loading}>
          {loading ? "Submitting..." : "Submit"}
        </button>
      </form>
      {message && <div className="mt-4 text-center text-purple-700 font-semibold">{message}</div>}
    </div>
  );
}

export default UploaderDashboard;
