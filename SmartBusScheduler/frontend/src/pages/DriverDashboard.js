// DriverDashboard.js
import React, { useState, useEffect } from "react";
import "leaflet/dist/leaflet.css";

function DriverDashboard() {
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch dynamic data (you can replace this with API call later)
  useEffect(() => {
    setTimeout(() => {
      setSchedule([
        {
          busNo: "101",
          time: "08:00 AM",
          busName: "City Express",
          stops: [
            { name: "Stop 1", coords: [28.6139, 77.209] },
            { name: "Stop 2", coords: [28.62, 77.23] },
            { name: "Stop 3", coords: [28.635, 77.25] },
            { name: "Stop 4", coords: [28.64, 77.26] },
          ],
        },
        {
          busNo: "202",
          time: "09:30 AM",
          busName: "Metro Link",
          stops: [
            { name: "Stop 1", coords: [28.7041, 77.1025] },
            { name: "Stop 2", coords: [28.71, 77.13] },
            { name: "Stop 3", coords: [28.72, 77.15] },
          ],
        },
      ]);
      setLoading(false);
    }, 1200);
  }, []);

  // ✅ Function to open Google Maps route
  const openInGoogleMaps = (stops) => {
    if (stops.length < 2) return alert("At least two stops needed for route");

    // Format the Google Maps route URL
    const origin = stops[0].coords.join(",");
    const destination = stops[stops.length - 1].coords.join(",");
    const waypoints = stops
      .slice(1, -1)
      .map((s) => s.coords.join(","))
      .join("|");

    const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}&waypoints=${waypoints}&travelmode=driving`;

    window.open(googleMapsUrl, "_blank"); // opens in new tab
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-lg text-gray-600 animate-pulse">
          Loading schedule...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-8 text-center">
        Allocated Bus Trips
      </h1>

      <div className="grid gap-6 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {schedule.map((trip, index) => (
          <div
            key={index}
            className="bg-white rounded-2xl shadow-md hover:shadow-xl transition-all duration-500 border border-gray-200 overflow-hidden p-5"
          >
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-lg font-semibold text-blue-700">
                {trip.busName}
              </h2>
              <span className="text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded-full">
                {trip.busNo}
              </span>
            </div>

            <p className="text-gray-600 mb-4">🕒 {trip.time}</p>

            <button
              onClick={() => openInGoogleMaps(trip.stops)}
              className="w-full bg-blue-600 text-white font-medium py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              View Route in Google Maps
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default DriverDashboard;