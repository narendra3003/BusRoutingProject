import React, { useState, useEffect } from "react";
import Calendar from "react-calendar";
import "react-calendar/dist/Calendar.css";
import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Default marker
const defaultIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

// Current stop marker
const currentIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const CustomerViewer = () => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [expandedBus, setExpandedBus] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");

  const schedules = [
    { busNo: "101", busName: "Green Express", time: "08:00 AM", route: ["Connaught Place", "Karol Bagh", "Patel Nagar", "Shastri Nagar"], currentLocation: "Patel Nagar" },
    { busNo: "202", busName: "City Rider", time: "09:30 AM", route: ["India Gate", "Khan Market", "AIIMS", "Hauz Khas"], currentLocation: "AIIMS" },
    { busNo: "303", busName: "Metro Link", time: "10:15 AM", route: ["Kashmere Gate", "Civil Lines", "Model Town", "Azadpur"], currentLocation: "Model Town" },
    { busNo: "404", busName: "Rapid Route", time: "11:00 AM", route: ["Lajpat Nagar", "Nehru Place", "Kalkaji", "Govindpuri"], currentLocation: "Kalkaji" },
    { busNo: "505", busName: "Capital Cruiser", time: "12:00 PM", route: ["Rajouri Garden", "Punjabi Bagh", "Ashok Vihar", "Shalimar Bagh"], currentLocation: "Ashok Vihar" },
  ];

  const routeCoords = {
    "Green Express": [[28.6315, 77.2167], [28.6512, 77.1904], [28.6519, 77.1711], [28.6694, 77.1916]],
    "City Rider": [[28.6129, 77.2295], [28.6005, 77.2273], [28.5672, 77.2100], [28.5494, 77.2017]],
    "Metro Link": [[28.6673, 77.2300], [28.6822, 77.2287], [28.7073, 77.1925], [28.7090, 77.1772]],
    "Rapid Route": [[28.5623, 77.2433], [28.5499, 77.2522], [28.5389, 77.2586], [28.5301, 77.2619]],
    "Capital Cruiser": [[28.6412, 77.1197], [28.6663, 77.1347], [28.6826, 77.1652], [28.7067, 77.1709]],
  };

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        setUserLocation([position.coords.latitude, position.coords.longitude]);
      });
    }
  }, []);

  const getDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  const handleToggle = (busNo) => {
    setExpandedBus(expandedBus === busNo ? null : busNo);
    setSearchTerm(""); // clear search if table clicked
  };

  // Filter routes for search or expanded bus
  const filteredBuses = Object.entries(routeCoords).filter(([busName]) => {
    if (searchTerm) {
      return schedules.find(
        (b) =>
          (b.busNo.toLowerCase().includes(searchTerm.toLowerCase()) ||
          b.busName.toLowerCase().includes(searchTerm.toLowerCase())) &&
          b.busName === busName
      );
    } else if (expandedBus) {
      const bus = schedules.find((b) => b.busNo === expandedBus);
      return bus && bus.busName === busName;
    }
    return true;
  });

  return (
    <div className="flex flex-col p-6 space-y-6">
      {/* Top Section */}
      <div className="flex space-x-6">
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
                  <tr onClick={() => handleToggle(bus.busNo)} className="cursor-pointer hover:bg-gray-100">
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
                            <li key={idx} className={stop === bus.currentLocation ? "font-bold text-green-600" : ""}>
                              {stop} {stop === bus.currentLocation && " (Current)"}
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
        <div className="w-1/3">
          <h2 className="text-xl font-bold mb-4">Select Date</h2>
          <Calendar onChange={setSelectedDate} value={selectedDate} className="border p-2 rounded-lg" />
          <p className="mt-2 text-gray-700">
            Showing schedule for: <span className="font-semibold">{selectedDate.toDateString()}</span>
          </p>
        </div>
      </div>

      {/* Map Section */}
      <div className="mt-8">
        <h2 className="text-xl font-bold mb-2">Bus Routes Map</h2>

        {/* Search Bar */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search by Bus No or Name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="border border-gray-400 rounded-lg p-2 w-full"
          />
        </div>

        <div className="h-[450px] w-full rounded-xl overflow-hidden shadow-lg">
          <MapContainer center={[28.6139, 77.209]} zoom={12} style={{ height: "100%", width: "100%" }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {filteredBuses.map(([busName, coords], index) => {
              const bus = schedules.find((b) => b.busName === busName);
              return (
                <React.Fragment key={busName}>
                  <Polyline
                    positions={coords}
                    color={["blue", "green", "red", "orange", "purple"][index % 5]}
                    weight={bus.busNo === expandedBus ? 6 : 3}
                  />
                  {coords.map((pos, idx) => {
                    const isCurrent = bus.currentLocation === bus.route[idx];
                    return (
                      <Marker key={idx} position={pos} icon={isCurrent ? currentIcon : defaultIcon}>
                        <Popup>
                          {busName} - Stop {idx + 1} - {bus.route[idx]} {isCurrent && " (Current)"}
                        </Popup>
                      </Marker>
                    );
                  })}
                </React.Fragment>
              );
            })}

            {userLocation && (
              <Marker position={userLocation}>
                <Popup>Your Location</Popup>
              </Marker>
            )}
          </MapContainer>
        </div>
      </div>
    </div>
  );
};

export default CustomerViewer;