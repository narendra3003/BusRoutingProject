import React, { useState } from "react";
import Calendar from "react-calendar"; // install with: npm install react-calendar
import "react-calendar/dist/Calendar.css";

function AdminDashboard() {
  const [file, setFile] = useState(null);
  const [schedule, setSchedule] = useState([]);
  const [expandedBus, setExpandedBus] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date());

  // Simulate dataset upload + schedule generation
  const handleUpload = () => {
    if (!file) {
      alert("Please upload a dataset first!");
      return;
    }
    // TODO: call backend API with the file
    // For now, dummy schedule
    setSchedule([
      {
        busNumber: "101",
        time: "09:00 AM",
        busName: "CityLink",
        routes: [
          "Central Station (current)",
          "Market Square",
          "University",
        ],
      },
      {
        busNumber: "202",
        time: "10:30 AM",
        busName: "MetroExpress",
        routes: [
          "Airport",
          "Tech Park (current)",
          "City Center",
        ],
      },
    ]);
    alert("Dataset uploaded successfully. Schedule generated!");
  };

  const toggleBus = (busNumber) => {
    setExpandedBus(expandedBus === busNumber ? null : busNumber);
  };

  return (
    <div className="p-6 space-y-8">
      {/* Dataset Uploader */}
      <div className="bg-white p-4 shadow rounded">
        <h2 className="text-xl font-bold mb-3">Upload Dataset</h2>
        <input
          type="file"
          accept=".csv,.xlsx"
          onChange={(e) => setFile(e.target.files[0])}
          className="mb-3"
        />
        <button
          onClick={handleUpload}
          className="bg-purple-600 text-white px-4 py-2 rounded"
        >
          Upload & Generate Schedule
        </button>
      </div>

      {/* Schedule Viewer */}
      {schedule.length > 0 && (
        <div className="bg-white p-4 shadow rounded">
          <h2 className="text-xl font-bold mb-3">Generated Schedule</h2>
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-purple-100 text-left">
                <th className="p-2 border">Bus Number</th>
                <th className="p-2 border">Time</th>
                <th className="p-2 border">Bus Name</th>
              </tr>
            </thead>
            <tbody>
              {schedule.map((bus) => (
                <React.Fragment key={bus.busNumber}>
                  <tr
                    className="cursor-pointer hover:bg-purple-50"
                    onClick={() => toggleBus(bus.busNumber)}
                  >
                    <td className="p-2 border">{bus.busNumber}</td>
                    <td className="p-2 border">{bus.time}</td>
                    <td className="p-2 border text-purple-700 font-semibold">
                      {bus.busName}
                    </td>
                  </tr>
                  {expandedBus === bus.busNumber && (
                    <tr>
                      <td colSpan="3" className="p-3 border bg-gray-50">
                        <ul className="list-disc pl-6 space-y-1">
                          {bus.routes.map((route, idx) => (
                            <li key={idx}>{route}</li>
                          ))}
                        </ul>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Calendar Section */}
      {schedule.length > 0 && (
        <div className="bg-white p-4 shadow rounded flex flex-col items-center">
          <h2 className="text-xl font-bold mb-3">Check Schedule by Date</h2>
          <Calendar
            onChange={setSelectedDate}
            value={selectedDate}
            className="mb-4"
          />
          <p className="text-gray-600">
            Showing schedule for:{" "}
            <span className="font-semibold">
              {selectedDate.toDateString()}
            </span>
          </p>
        </div>
      )}

      {/* Driver Allotment */}
      {schedule.length > 0 && (
        <div className="bg-white p-4 shadow rounded">
          <h2 className="text-xl font-bold mb-3">Driver Allotment</h2>
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-purple-100 text-left">
                <th className="p-2 border">Driver Name</th>
                <th className="p-2 border">Bus Number</th>
                <th className="p-2 border">Shift Time</th>
                <th className="p-2 border">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="p-2 border">John Doe</td>
                <td className="p-2 border">101</td>
                <td className="p-2 border">09:00 AM - 01:00 PM</td>
                <td className="p-2 border">Assigned</td>
              </tr>
              <tr>
                <td className="p-2 border">Alice Smith</td>
                <td className="p-2 border">202</td>
                <td className="p-2 border">10:30 AM - 02:30 PM</td>
                <td className="p-2 border">Assigned</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
