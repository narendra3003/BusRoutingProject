import React, { useEffect, useState } from "react";

function LeaveApprovalPage() {
  const [leaves, setLeaves] = useState([]);
  const [activeTab, setActiveTab] = useState("pending");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // -------------------------
  // MOCK DATA (single source of truth)
  // -------------------------
  const [allLeaves, setAllLeaves] = useState([
    {
      id: 1,
      driver_name: "John",
      start_date: "2026-04-10",
      end_date: "2026-04-12",
      reason: "Medical",
      status: "pending",
    },
    {
      id: 2,
      driver_name: "Rahul",
      start_date: "2026-04-15",
      end_date: "2026-04-18",
      reason: "Family function",
      status: "pending",
    },
    {
      id: 3,
      driver_name: "Mike",
      start_date: "2026-04-01",
      end_date: "2026-04-03",
      reason: "Personal",
      status: "granted",
    },
    {
      id: 4,
      driver_name: "Amit",
      start_date: "2026-03-28",
      end_date: "2026-03-30",
      reason: "Emergency",
      status: "rejected",
    },
  ]);

  // -------------------------
  // FETCH (FILTER MOCK)
  // -------------------------
  const fetchLeaves = (status) => {
    setLoading(true);

    setTimeout(() => {
      const filtered = allLeaves.filter((l) => l.status === status);
      setLeaves(filtered);
      setLoading(false);
    }, 300);
  };

  useEffect(() => {
    fetchLeaves(activeTab);
  }, [activeTab, allLeaves]);

  // -------------------------
  // APPROVE
  // -------------------------
  const approveLeave = (id) => {
    const updated = allLeaves.map((l) =>
      l.id === id ? { ...l, status: "granted" } : l
    );

    setAllLeaves(updated);
    setMessage("Leave approved ");
  };

  // -------------------------
  // REJECT
  // -------------------------
  const rejectLeave = (id) => {
    const updated = allLeaves.map((l) =>
      l.id === id ? { ...l, status: "rejected" } : l
    );

    setAllLeaves(updated);
    setMessage("Leave rejected");
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