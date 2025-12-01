import React, { useState } from "react";

function ScheduleTable({ schedule, onEditSchedule, onDeleteSchedule }) {
  const [editingIndex, setEditingIndex] = useState(null);
  const [editData, setEditData] = useState({});

  if (!schedule.length) return null;

  const handleEditClick = (index) => {
    setEditingIndex(index);
    setEditData(schedule[index]);
  };

  const handleSaveClick = () => {
    onEditSchedule(editingIndex, editData);
    setEditingIndex(null);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setEditData({ ...editData, [name]: value });
  };

  return (
    <div className="bg-white p-4 shadow rounded">
      <h2 className="text-xl font-bold mb-3">Bus Schedule</h2>
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-blue-100 text-left">
            <th className="p-2 border">Route ID</th>
            <th className="p-2 border">Driver ID</th>
            <th className="p-2 border">Bus ID</th>
            <th className="p-2 border">Start Time</th>
            <th className="p-2 border">End Time</th>
            {/* <th className="p-2 border">Actions</th> */}
          </tr>
        </thead>
        <tbody>
          {schedule.map((s, index) => (
            <tr key={index} className="hover:bg-gray-50">
              {editingIndex === index ? (
                <>
                  <td className="p-2 border">
                    <input
                      name="route_id"
                      value={editData.route_id}
                      onChange={handleChange}
                      className="border p-1 rounded w-full"
                    />
                  </td>
                  <td className="p-2 border">
                    <input
                      name="assigned_driver_id"
                      value={editData.assigned_driver_id}
                      onChange={handleChange}
                      className="border p-1 rounded w-full"
                    />
                  </td>
                  <td className="p-2 border">
                    <input
                      name="bus_id"
                      value={editData.bus_id}
                      onChange={handleChange}
                      className="border p-1 rounded w-full"
                    />
                  </td>
                  <td className="p-2 border">
                    <input
                      type="datetime-local"
                      name="planned_start"
                      value={new Date(editData.planned_start)
                        .toISOString()
                        .slice(0, 16)}
                      onChange={handleChange}
                      className="border p-1 rounded w-full"
                    />
                  </td>
                  <td className="p-2 border">
                    <input
                      type="datetime-local"
                      name="planned_end"
                      value={new Date(editData.planned_end)
                        .toISOString()
                        .slice(0, 16)}
                      onChange={handleChange}
                      className="border p-1 rounded w-full"
                    />
                  </td>
                  <td className="p-2 border text-center">
                    <button
                      onClick={handleSaveClick}
                      className="bg-green-500 text-white px-3 py-1 rounded mr-2"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setEditingIndex(null)}
                      className="bg-gray-400 text-white px-3 py-1 rounded"
                    >
                      Cancel
                    </button>
                  </td>
                </>
              ) : (
                <>
                  <td className="p-2 border">{s.route_id}</td>
                  <td className="p-2 border">{s.assigned_driver_id}</td>
                  <td className="p-2 border">{s.bus_id}</td>
                  <td className="p-2 border">
                    {new Date(s.planned_start).toLocaleString()}
                  </td>
                  <td className="p-2 border">
                    {new Date(s.planned_end).toLocaleString()}
                  </td>
                  {/* <td className="p-2 border text-center">
                    <button
                      onClick={() => handleEditClick(index)}
                      className="bg-blue-500 text-white px-3 py-1 rounded mr-2"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => onDeleteSchedule(index)}
                      className="bg-red-500 text-white px-3 py-1 rounded"
                    >
                      Delete
                    </button>
                  </td> */}
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ScheduleTable;