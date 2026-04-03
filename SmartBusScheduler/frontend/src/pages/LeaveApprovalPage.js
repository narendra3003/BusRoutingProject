import React, { useEffect, useState } from "react";

function LeaveApprovalPage() {
  const [leaves, setLeaves] = useState([]);
  const [activeTab, setActiveTab] = useState("pending");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // -------------------------
  // FETCH LEAVES
  // -------------------------
  const fetchLeaves = async (status) => {
    try {
      setLoading(true);

      const res = await fetch(
        `http://localhost:8000/admin/leaves?status=${status}`,
        {
          headers: {
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
        }
      );

      if (!res.ok) throw new Error("Failed to fetch leaves");

      const data = await res.json();
      setLeaves(data);

    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaves(activeTab);
  }, [activeTab]);

  // -------------------------
  // APPROVE
  // -------------------------
  const approveLeave = async (id) => {
    try {
      await fetch(
        `http://localhost:8000/admin/leaves/${id}/approve`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
        }
      );

      setMessage("Leave approved");
      fetchLeaves(activeTab);
    } catch {
      setMessage("Approve failed");
    }
  };

  // -------------------------
  // REJECT
  // -------------------------
  const rejectLeave = async (id) => {
    try {
      await fetch(
        `http://localhost:8000/admin/leaves/${id}/reject`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
        }
      );

      setMessage("Leave rejected");
      fetchLeaves(activeTab);
    } catch {
      setMessage("Reject failed");
    }
  };

  // -------------------------
  // UI
  // -------------------------
  return (
    <div className="p-6 space-y-6">

      <h1 className="text-2xl font-bold">Driver Leave Approval</h1>

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

      {/* TABLE */}
      <div className="bg-white p-6 shadow rounded">

        {loading && <p>Loading...</p>}

        <table className="w-full border text-center">
          <thead className="bg-gray-100">
            <tr>
              <th>Driver</th>
              <th>Start Date</th>
              <th>End Date</th>
              <th>Reason</th>
              <th>Status</th>
              {activeTab === "pending" && <th>Actions</th>}
            </tr>
          </thead>

          <tbody>
            {leaves.map((l) => (
              <tr key={l.id} className="border-t">
                <td>{l.driver_name}</td>
                <td>{l.start_date}</td>
                <td>{l.end_date}</td>
                <td>{l.reason}</td>
                <td>{l.status}</td>

                {activeTab === "pending" && (
                  <td className="space-x-2">
                    <button
                      onClick={() => approveLeave(l.id)}
                      className="bg-green-600 text-white px-2 py-1"
                    >
                      Approve
                    </button>

                    <button
                      onClick={() => rejectLeave(l.id)}
                      className="bg-red-600 text-white px-2 py-1"
                    >
                      Reject
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>

        {leaves.length === 0 && !loading && (
          <p className="text-gray-500 mt-4">
            No records found
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

export default LeaveApprovalPage;