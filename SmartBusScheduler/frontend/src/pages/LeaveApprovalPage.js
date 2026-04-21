import React, { useEffect, useState } from "react";
import AdminLayout from "./AdminLayout";
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

      //setMessage("Leave approved");
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

      //setMessage("Leave rejected");
      fetchLeaves(activeTab);
    } catch {
      setMessage("Reject failed");
    }
  };

  // -------------------------
  // UI
  // -------------------------
  return (
    <AdminLayout>
    <div className="p-6 space-y-6">

      <h1 className="text-2xl font-bold">Driver Leave Approval</h1>

      {/* TABS */}
      <div className="flex gap-2 bg-gray-100 p-1 rounded-lg w-fit mb-4">
        {["pending", "granted", "rejected"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200
              ${
                activeTab === tab
                  ? "bg-white shadow text-purple-600"
                  : "text-gray-600 hover:text-gray-800"
              }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* TABLE */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden">

        {loading && <p>Loading...</p>}

        <table className="w-full text-sm text-gray-700">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs tracking-wider">
            <tr>
              <th className="px-6 py-3 text-left">Driver</th>
              <th className="px-6 py-3">Start Date</th>
              <th className="px-6 py-3">End Date</th>
              <th className="px-6 py-3 text-left">Reason</th>
              <th className="px-6 py-3">Status</th>
              {activeTab === "pending" && (
                <th className="px-6 py-3 text-center">Actions</th>
              )}
            </tr>
          </thead>

          <tbody className="hover:bg-gray-50 transition duration-150">
            {leaves.map((l) => (
              <tr key={l.id} className="border-t">
                <td className="px-6 py-4 font-medium text-gray-900">{l.driver_name}</td>
                <td className="px-6 py-4 text-center">{l.start_date}</td>
                <td className="px-6 py-4 text-center">{l.end_date}</td>
                <td className="px-6 py-4 text-left max-w-xs truncate">{l.reason}</td>
                <td className="px-6 py-4 text-center">
                  <span
                    className={`px-3 py-1 text-xs font-semibold rounded-full ${
                      l.status === "approved"
                        ? "bg-green-100 text-green-700"
                        : l.status === "rejected"
                        ? "bg-red-100 text-red-700"
                        : "bg-yellow-100 text-yellow-700"
                    }`}
                  >
                    {l.status}
                  </span>
                </td>

                {activeTab === "pending" && (
                  <td className="px-6 py-4 flex justify-center gap-2">
                    <button
                      onClick={() => approveLeave(l.id)}
                      className="px-4 py-1.5 border border-green-500 text-green-600 text-sm font-semibold rounded-lg hover:bg-green-50 transition-all duration-200"
                    >
                      Approve
                    </button>

                    <button
                      onClick={() => rejectLeave(l.id)}
                      className="px-4 py-1.5 border border-red-500 text-red-600 text-sm font-semibold rounded-lg hover:bg-red-50 transition-all duration-200 ml-2"
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
    </AdminLayout>
  );
}

export default LeaveApprovalPage;