import React, { useState } from "react";
import Calendar from "react-calendar"; // npm install react-calendar
import "react-calendar/dist/Calendar.css";

const CustomerViewer = () => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [expandedBus, setExpandedBus] = useState(null);

  // Dummy schedule data (replace with API call later)
  const schedules = [
    {
      busNo: "101",
      busName: "Green Express",
      time: "08:00 AM",
      route: ["Stop A", "Stop B", "Stop C", "Stop D"],
      currentLocation: "Stop B",
    },
    {
      busNo: "202",
      busName: "City Rider",
      time: "09:30 AM",
      route: ["Stop X", "Stop Y", "Stop Z"],
      currentLocation: "Stop Y",
    },
  ];

  const handleToggle = (busNo) => {
    setExpandedBus(expandedBus === busNo ? null : busNo);
  };

  return (
    <div className="flex p-6 space-x-6">
      {/* Left: Schedule Table */}
      <div className="w-2/3">
        <h2 className="text-xl font-bold mb-4">Bus Schedule</h2>
        <table className="w-full border border-gray-300">
          <thead>
            <tr className="bg-gray-200">
              <th className="border p-2">Bus No</th>
              <th className="border p-2">Bus Name</th>
              <th className="border p-2">Time</th>
            </tr>
          </thead>
          <tbody>
            {schedules.map((bus) => (
              <React.Fragment key={bus.busNo}>
                <tr
                  onClick={() => handleToggle(bus.busNo)}
                  className="cursor-pointer hover:bg-gray-100"
                >
                  <td className="border p-2">{bus.busNo}</td>
                  <td className="border p-2">{bus.busName}</td>
                  <td className="border p-2">{bus.time}</td>
                </tr>
                {expandedBus === bus.busNo && (
                  <tr>
                    <td colSpan="3" className="border p-2 bg-gray-50">
                      <strong>Route:</strong>
                      <ul className="list-disc ml-6">
                        {bus.route.map((stop, idx) => (
                          <li
                            key={idx}
                            className={
                              stop === bus.currentLocation
                                ? "font-bold text-green-600"
                                : ""
                            }
                          >
                            {stop}
                            {stop === bus.currentLocation && " (Current)"}
                          </li>
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

      {/* Right: Calendar */}
      <div className="w-1/3">
        <h2 className="text-xl font-bold mb-4">Select Date</h2>
        <Calendar
          onChange={setSelectedDate}
          value={selectedDate}
          className="border p-2 rounded-lg"
        />
        <p className="mt-2 text-gray-700">
          Showing schedule for:{" "}
          <span className="font-semibold">
            {selectedDate.toDateString()}
          </span>
        </p>
      </div>
    </div>
  );
};

export default CustomerViewer;