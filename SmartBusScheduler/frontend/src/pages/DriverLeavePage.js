import React, { useEffect, useState } from "react";

function DriverLeavePage() {
  const [leaveForm, setLeaveForm] = useState({
    start_date: "",
    end_date: "",
    reason: "",
  });

  const [leaves, setLeaves] = useState([]);
  const [activeTab, setActiveTab] = useState("pending");

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // -------------------------
  // FETCH LEAVES
  // -------------------------
  const fetchLeaves = async () => {
    try {
      const token = sessionStorage.getItem("token");

      const res = await fetch("http://localhost:8000/driver/leaves", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) throw new Error("Failed to fetch leaves");

      const data = await res.json();
      setLeaves(data);

    } catch (err) {
      setMessage(err.message);
    }
  };

  useEffect(() => {
    fetchLeaves();
  }, []);

  // -------------------------
  // APPLY LEAVE
  // -------------------------
  const applyLeave = async () => {
    if (!leaveForm.start_date || !leaveForm.end_date) {
      return setMessage("Select dates");
    }

    try {
      setLoading(true);
      const token = sessionStorage.getItem("token");

      const res = await fetch("http://localhost:8000/driver/leaves/apply", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(leaveForm),
      });

      if (!res.ok) throw new Error("Failed to apply leave");

      setMessage("Leave applied successfully!");
      setLeaveForm({ start_date: "", end_date: "", reason: "" });

      fetchLeaves();

    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // CANCEL LEAVE
  // -------------------------
  const cancelLeave = async (id) => {
    try {
      const token = sessionStorage.getItem("token");

      const res = await fetch(
        `http://localhost:8000/driver/leaves/${id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!res.ok) throw new Error("Cancel failed");

      setMessage("Leave cancelled");
      fetchLeaves();

    } catch (err) {
      setMessage(err.message);
    }
  };

  // -------------------------
  // FILTERED LEAVES
  // -------------------------
  const filteredLeaves = leaves.filter(
    (l) => l.status === activeTab
  );

  // -------------------------
  // UI
  // -------------------------
  return (
    <div className="p-6 space-y-8">

      {/* HEADER */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Manage Leaves</h1>

        <button
          onClick={() => window.location.href = "/driver"}
          className="bg-gray-600 text-white px-4 py-2 rounded"
        >
          Back
        </button>
      </div>

      {/* APPLY LEAVE */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">Apply Leave</h2>

        <div className="grid grid-cols-3 gap-4">

          <input
            type="date"
            value={leaveForm.start_date}
            onChange={(e) =>
              setLeaveForm({
                ...leaveForm,
                start_date: e.target.value,
              })
            }
            className="border p-2"
          />

          <input
            type="date"
            value={leaveForm.end_date}
            onChange={(e) =>
              setLeaveForm({
                ...leaveForm,
                end_date: e.target.value,
              })
            }
            className="border p-2"
          />

          <input
            placeholder="Reason"
            value={leaveForm.reason}
            onChange={(e) =>
              setLeaveForm({
                ...leaveForm,
                reason: e.target.value,
              })
            }
            className="border p-2"
          />

        </div>

        <button
          onClick={applyLeave}
          className="mt-4 bg-red-600 text-white px-4 py-2 rounded"
          disabled={loading}
        >
          Apply Leave
        </button>
      </div>

      {/* TABS */}
      <div className="flex gap-4">
        {["pending", "granted", "rejected"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded ${
              activeTab === tab
                ? "bg-purple-600 text-white"
                : "bg-gray-200"
            }`}
          >
            {tab.toUpperCase()}
          </button>
        ))}
      </div>

      {/* LEAVES TABLE */}
      <div className="bg-white p-6 shadow rounded">

        <table className="w-full border text-center">
          <thead className="bg-gray-100">
            <tr>
              <th>Start</th>
              <th>End</th>
              <th>Reason</th>
              <th>Status</th>
              {activeTab === "pending" && <th>Action</th>}
            </tr>
          </thead>

          <tbody>
            {filteredLeaves.map((l) => (
              <tr key={l.id} className="border-t">
                <td>{l.start_date}</td>
                <td>{l.end_date}</td>
                <td>{l.reason}</td>
                <td>{l.status}</td>

                {activeTab === "pending" && (
                  <td>
                    <button
                      onClick={() => cancelLeave(l.id)}
                      className="bg-red-500 text-white px-2 py-1"
                    >
                      Cancel
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>

        {filteredLeaves.length === 0 && (
          <p className="text-gray-500 mt-4">
            No leaves found
          </p>
        )}
      </div>

      {/* MESSAGE */}
      {message && (
        <p className="text-purple-600">{message}</p>
      )}

    </div>
  );
}

export default DriverLeavePage;