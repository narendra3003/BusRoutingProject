// DriverDashboard.js
import React, { useState, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
} from "react-leaflet";
import L from "leaflet";
import Calendar from "react-calendar";
import "leaflet/dist/leaflet.css";
import "react-calendar/dist/Calendar.css";

// Fix Leaflet marker icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png",
  iconUrl:
    "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png",
});

function DriverDashboard() {
  const [schedule, setSchedule] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [dateStatusMap, setDateStatusMap] = useState({});
  const [summary, setSummary] = useState(null);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [loading, setLoading] = useState(true);

  // ===========================
  // API CALLS
  // ===========================

  useEffect(() => {
    fetchSchedule();
    fetchNotifications();
    fetchSummary();
  }, [selectedDate]);

  useEffect(() => {
    fetchCalendarStatus();
  }, []);

  const fetchSchedule = async () => {
    try {
      setLoading(true);
      const token = sessionStorage.getItem("token");
      const formattedDate = selectedDate.toISOString().split("T")[0];

      const res = await fetch(
        `http://localhost:8000/drivers/schedule?date=${formattedDate}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          }
        }
      );
      const data = await res.json();

      setSchedule(data.trips);
    } catch (err) {
      console.error("Error fetching schedule", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchNotifications = async () => {
    try {
      const token = sessionStorage.getItem("token");
      const res = await fetch("http://localhost:8000/drivers/notifications", {
        headers: {
          Authorization: `Bearer ${token}`,
        }
      });
      const data = await res.json();

      setNotifications(data.notifications);
    } catch (err) {
      console.error("Error fetching notifications", err);
    }
  }

  const fetchCalendarStatus = async () => {
    try {
      const token = sessionStorage.getItem("token");
      const res = await fetch("http://localhost:8000/drivers/calendar-status", {
        headers: {
          Authorization: `Bearer ${token}`,
        }
      });
      const data = await res.json();

      setDateStatusMap(data.statusMap);
    } catch (err) {
      console.error("Error fetching calendar", err);
    }
  };

  const fetchSummary = async () => {
    try {
      const token = sessionStorage.getItem("token");
      const formattedDate = selectedDate.toISOString().split("T")[0];
      const res = await fetch(
        `http://localhost:8000/drivers/summary?date=${formattedDate}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          }
        }
      );
      const data = await res.json();

      setSummary(data);
    } catch (err) {
      console.error("Error fetching summary", err);
    }
  };

  const getTileClassName = ({ date, view }) => {
    if (view !== "month") return "";

    if (date.toDateString() === selectedDate.toDateString()) {
      return "border-2 border-blue-500 rounded-lg";
    }

    return "";
  };

  const getTileContent = ({ date, view }) => {
    if (view !== "month") return null;

    const key = date.toISOString().split("T")[0];
    const status = dateStatusMap[key];

    if (!status) return null;

    const dotStyles = {
      assigned: "bg-green-500",
      holiday: "bg-red-500",
      "leave-applied": "bg-yellow-400",
    };

    return (
      <div className="flex justify-center mt-1">
        <div className={`w-2 h-2 rounded-full ${dotStyles[status]}`} />
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        Loading schedule...
      </div>
    );
  }

  const todaysTrips = schedule;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">

      {/* HEADER */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Driver Dashboard</h1>

          <button
            onClick={() => window.location.href = "/driver/leave"}
            className="bg-red-500 text-white px-4 py-2 rounded-lg shadow"
          >
            Apply Leave
          </button>
        </div>
      </div>

      {/* TOP SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[80vh]">

        {/* SUMMARY */}
        <div className="bg-white rounded-2xl shadow-md p-6 flex flex-col">
          <h2 className="text-xl font-semibold mb-4">Daily Summary</h2>

          <p>📅 {selectedDate.toDateString()}</p>

          <div className="space-y-3 mt-4">
            <div className="p-3 bg-blue-50 rounded-lg">
              🚍 Trips Assigned: {summary?.totalTrips || 0}
            </div>

            <div className="p-3 bg-green-50 rounded-lg">
              ⏱ Total Duty Hours: {summary?.totalHours || 0} hrs
            </div>

            <div className="p-3 bg-yellow-50 rounded-lg">
              🔁 Shifts: {summary?.shifts?.join(" / ") || "-"}
            </div>

            <div className="p-3 bg-purple-50 rounded-lg">
              📍 First Route: {summary?.firstRoute || "-"}
            </div>
          </div>
        </div>

        {/* CALENDAR */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Select Date</h2>

          <Calendar
            onChange={setSelectedDate}
            value={selectedDate}
            tileContent={getTileContent}
            tileClassName={getTileClassName}
          />
          <button
            onClick={() => window.location.href = "/driver/leave"}
            className="mt-4 w-full bg-yellow-500 text-white py-2 rounded"
          >
            Manage Leaves
          </button>

          <div className="mt-6 border-t pt-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              Assigned
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              Approved Leaves
              <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
              Applied Leaves
            </div>
          </div>
        </div>
      </div>

      {/* TRIPS */}
      <div className="mt-10">
        <h2 className="text-2xl font-semibold mb-4">
          Trips for Selected Date
        </h2>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {todaysTrips.map((trip) => (
            <div key={trip.id} className="bg-white rounded-2xl shadow-md p-5">
              <div className="flex justify-between mb-3">
                <h3 className="text-lg font-semibold text-blue-700">
                  {trip.busName}
                </h3>
                <span className="bg-blue-100 px-3 py-1 rounded-full">
                  {trip.busNo}
                </span>
              </div>

              <p>🕒 {trip.time}</p>
              <p className="text-green-600 mb-4">
                Status: {trip.status}
              </p>

              <button
                onClick={() => setSelectedTrip(trip)}
                className="w-full bg-blue-600 text-white py-2 rounded-lg"
              >
                View Route
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* NOTIFICATIONS */}
      <div className="mt-10 bg-white rounded-xl shadow-md p-4">
        <h2 className="text-lg font-semibold mb-3">
          Updates & Leaves
        </h2>

        {notifications.map((note) => (
          <div key={note.id} className="border-b py-2 text-sm">
            🔔 {note.message}
          </div>
        ))}
      </div>

      {/* MAP MODAL */}
      {selectedTrip && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex justify-center items-center z-[9999]">
          <div className="relative bg-white w-11/12 h-5/6 rounded-xl overflow-hidden">

            <button
              onClick={() => setSelectedTrip(null)}
              className="absolute top-4 right-4 z-[10000] bg-red-600 text-white px-4 py-2 rounded-lg"
            >
              ✕
            </button>

            <MapContainer
              center={selectedTrip.stops[0].coords}
              zoom={13}
              style={{ height: "100%", width: "100%" }}
            >
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

              {selectedTrip.stops.map((stop, index) => (
                <Marker key={index} position={stop.coords}>
                  <Popup>{stop.name}</Popup>
                </Marker>
              ))}

              <Polyline
                positions={selectedTrip.stops.map((s) => s.coords)} color="blue"
              />
            </MapContainer>
          </div>
        </div>
      )}
    </div>
  );
}

export default DriverDashboard;