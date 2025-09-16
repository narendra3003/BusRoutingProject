// DriverDashboard.js
import React, { useState } from "react";
import { MapContainer, TileLayer, Marker, Polyline, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Fix leaflet’s default marker issue
import L from "leaflet";
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

function DriverDashboard() {
  const [expanded, setExpanded] = useState(null);

  // Dummy driver schedule data
  const schedule = [
    {
      busNo: "101",
      time: "08:00 AM",
      busName: "City Express",
      stops: [
        { name: "Stop 1", coords: [28.6139, 77.209] },
        { name: "Stop 2", coords: [28.62, 77.23] },
        { name: "Stop 3", coords: [28.635, 77.25] },
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
  ];

  const toggleExpand = (index) => {
    setExpanded(expanded === index ? null : index);
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Driver Schedule</h1>

      <table className="w-full border border-gray-300">
        <thead>
          <tr className="bg-gray-200">
            <th className="p-2 border">Bus No</th>
            <th className="p-2 border">Time</th>
            <th className="p-2 border">Bus Name</th>
          </tr>
        </thead>
        <tbody>
          {schedule.map((trip, index) => (
            <React.Fragment key={index}>
              <tr className="text-center">
                <td className="p-2 border">{trip.busNo}</td>
                <td className="p-2 border">{trip.time}</td>
                <td
                  className="p-2 border text-blue-600 cursor-pointer hover:underline"
                  onClick={() => toggleExpand(index)}
                >
                  {trip.busName}
                </td>
              </tr>

              {/* Expand row for stops + map */}
              {expanded === index && (
                <tr>
                  <td colSpan="3" className="p-4 border bg-gray-50">
                    <div className="mb-3">
                      <strong>Stops:</strong>
                      <ul className="list-disc list-inside">
                        {trip.stops.map((stop, i) => (
                          <li key={i}>{stop.name}</li>
                        ))}
                      </ul>
                    </div>

                    <MapContainer
                      center={trip.stops[0].coords}
                      zoom={13}
                      style={{ height: "300px", width: "100%" }}
                    >
                      <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution="&copy; OpenStreetMap contributors"
                      />
                      {trip.stops.map((stop, i) => (
                        <Marker key={i} position={stop.coords}>
                          <Popup>{stop.name}</Popup>
                        </Marker>
                      ))}
                      <Polyline
                        positions={trip.stops.map((stop) => stop.coords)}
                        color="blue"
                      />
                    </MapContainer>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DriverDashboard;