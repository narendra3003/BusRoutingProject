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
import "leaflet/dist/leaflet.css";

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
  const [loading, setLoading] = useState(true);
  const [isAvailable, setIsAvailable] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(null);

  // Delhi 8-Hour Schedule
  useEffect(() => {
    setTimeout(() => {
      const data = [
        {
          id: 1,
          busNo: "DL-101",
          time: "08:00 AM - 09:00 AM",
          busName: "Connaught Place → Karol Bagh",
          status: "Upcoming",
          stops: [
            { name: "Connaught Place", coords: [28.6315, 77.2167] },
            { name: "Rajiv Chowk Metro", coords: [28.6328, 77.2197] },
            { name: "Karol Bagh", coords: [28.6519, 77.1909] },
          ],
        },
        {
          id: 2,
          busNo: "DL-102",
          time: "09:30 AM - 10:30 AM",
          busName: "Karol Bagh → AIIMS",
          status: "Upcoming",
          stops: [
            { name: "Karol Bagh", coords: [28.6519, 77.1909] },
            { name: "Pusa Road", coords: [28.6425, 77.184] },
            { name: "AIIMS Delhi", coords: [28.5672, 77.21] },
          ],
        },
        {
          id: 3,
          busNo: "DL-103",
          time: "11:00 AM - 12:00 PM",
          busName: "AIIMS → Nehru Place",
          status: "Upcoming",
          stops: [
            { name: "AIIMS Delhi", coords: [28.5672, 77.21] },
            { name: "South Extension", coords: [28.5733, 77.2203] },
            { name: "Nehru Place", coords: [28.5494, 77.2519] },
          ],
        },
        {
          id: 4,
          busNo: "DL-104",
          time: "12:30 PM - 01:30 PM",
          busName: "Nehru Place → Lajpat Nagar",
          status: "Upcoming",
          stops: [
            { name: "Nehru Place", coords: [28.5494, 77.2519] },
            { name: "Kalkaji", coords: [28.5423, 77.2588] },
            { name: "Lajpat Nagar", coords: [28.5677, 77.2433] },
          ],
        },
        {
          id: 5,
          busNo: "DL-105",
          time: "02:00 PM - 03:00 PM",
          busName: "Lajpat Nagar → India Gate",
          status: "Upcoming",
          stops: [
            { name: "Lajpat Nagar", coords: [28.5677, 77.2433] },
            { name: "Pragati Maidan", coords: [28.6131, 77.242] },
            { name: "India Gate", coords: [28.6129, 77.2295] },
          ],
        },
        {
          id: 6,
          busNo: "DL-106",
          time: "03:30 PM - 04:00 PM",
          busName: "India Gate → Kashmere Gate",
          status: "Upcoming",
          stops: [
            { name: "India Gate", coords: [28.6129, 77.2295] },
            { name: "ITO", coords: [28.628, 77.241] },
            { name: "Kashmere Gate", coords: [28.6675, 77.2281] },
          ],
        },
      ];

      setSchedule(data);

      setNotifications([
        {
          id: 1,
          message: "6 trips assigned for today's 8-hour duty.",
        },
      ]);

      setLoading(false);
    }, 1000);
  }, []);

  const toggleAvailability = () => {
    setIsAvailable(!isAvailable);
    setNotifications((prev) => [
      {
        id: Date.now(),
        message: `You are now ${
          !isAvailable ? "Available" : "Not Available"
        }`,
      },
      ...prev,
    ]);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        Loading schedule...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Driver Dashboard</h1>

        <button
          onClick={toggleAvailability}
          className={`px-4 py-2 rounded-full text-white ${
            isAvailable ? "bg-green-600" : "bg-red-600"
          }`}
        >
          {isAvailable ? "Available" : "Not Available"}
        </button>
      </div>

      {/* Notifications */}
      <div className="bg-white rounded-xl shadow-md p-4 mb-8">
        <h2 className="text-xl font-semibold mb-3">Notifications</h2>
        {notifications.map((note) => (
          <div key={note.id} className="border-b py-2">
            🔔 {note.message}
          </div>
        ))}
      </div>

      {/* Schedule */}
      <h2 className="text-2xl font-semibold mb-4">Allotted Schedule</h2>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {schedule.map((trip) => (
          <div
            key={trip.id}
            className="bg-white rounded-2xl shadow-md p-5"
          >
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
              className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
            >
              View Route
            </button>
          </div>
        ))}
      </div>

{/* MAP MODAL */}
{selectedTrip && (
  <div className="fixed inset-0 bg-black bg-opacity-60 flex justify-center items-center z-[9999]">
    
    <div className="relative bg-white w-11/12 h-5/6 rounded-xl overflow-hidden shadow-2xl">
      
      {/* Close Button */}
      <button
        onClick={() => setSelectedTrip(null)}
        className="absolute top-4 right-4 z-[10000] bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg shadow-lg"
      >
        ✕ 
      </button>

      {/* Map */}
      <MapContainer
        center={selectedTrip.stops[0].coords}
        zoom={13}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {selectedTrip.stops.map((stop, index) => (
          <Marker key={index} position={stop.coords}>
            <Popup>{stop.name}</Popup>
          </Marker>
        ))}

        <Polyline
          positions={selectedTrip.stops.map((s) => s.coords)}
          color="blue"
        />
      </MapContainer>

    </div>
  </div>
)}
    </div>
  );
}

export default DriverDashboard;