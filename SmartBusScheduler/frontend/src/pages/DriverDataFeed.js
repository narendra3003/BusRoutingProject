import React, { useEffect, useState } from "react";
import AdminLayout from "./AdminLayout";
function DriverDataFeed() {
  const [drivers, setDrivers] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [search, setSearch] = useState("");

  const [newDriver, setNewDriver] = useState({
    name: "",
    email: "",
    phone: "",
    license_no: "",
    experience_years: "",
    joining_date: "",
  });

  const [message, setMessage] = useState("");

  // -------------------------
  // FETCH DRIVERS
  // -------------------------
  const fetchDrivers = async () => {
    try {
      const res = await fetch("http://localhost:8000/admin/drivers", {
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
        },
      });

      const data = await res.json();
      setDrivers(data);

      /*
      RESPONSE:
      [
        {
          user_id: 1,
          name: "John",
          email: "...",
          phone: "...",
          license_no: "XYZ",
          experience_years: 5,
          status: "active"
        }
      ]
      */
    } catch {
      setMessage("Failed to fetch drivers");
    }
  };

  useEffect(() => {
    fetchDrivers();
  }, []);

  // -------------------------
  // ADD DRIVER
  // -------------------------
  const addDriver = async () => {
    if (
      !newDriver.name ||
      !newDriver.email ||
      !newDriver.license_no
    ) {
      return setMessage("Name, email, license required");
    }

    try {
      await fetch("http://localhost:8000/admin/drivers", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
        },
        body: JSON.stringify(newDriver),

        /*
        REQUEST:
        {
          name,
          email,
          phone,
          license_no,
          experience_years,
          joining_date
        }

        BACKEND:
        - create user (role=driver)
        - create driver row
        */
      });

      setMessage("Driver added!");
      setNewDriver({
        name: "",
        email: "",
        phone: "",
        license_no: "",
        experience_years: "",
        joining_date: "",
      });

      fetchDrivers();
    } catch {
      setMessage("Failed to add driver");
    }
  };

  // -------------------------
  // UPDATE DRIVER
  // -------------------------
  const updateDriver = async () => {
    try {
      await fetch(
        `http://localhost:8000/admin/drivers/${selectedDriver.user_id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
          body: JSON.stringify(selectedDriver),
        }
      );

      setMessage("Updated!");
      setSelectedDriver(null);
      fetchDrivers();
    } catch {
      setMessage("Update failed");
    }
  };

  // -------------------------
  // TOGGLE STATUS
  // -------------------------
  const toggleStatus = async (driver) => {
    const updated = {
      ...driver,
      status: driver.status === "active" ? "inactive" : "active",
    };

    try {
      await fetch(
        `http://localhost:8000/admin/drivers/${driver.user_id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${sessionStorage.getItem("token")}`,
          },
          body: JSON.stringify(updated),
        }
      );

      fetchDrivers();
    } catch {
      setMessage("Status update failed");
    }
  };

  // -------------------------
  // FILTER
  // -------------------------
  const filteredDrivers = drivers.filter((d) =>
    d.name.toLowerCase().includes(search.toLowerCase())
  );

  // -------------------------
  // UI
  // -------------------------
  return (
    <AdminLayout>
    <div className="p-6 space-y-8">

      <h1 className="text-2xl font-bold">Drivers Management</h1>

      {/* ADD DRIVER */}
      <div className="bg-[#E6F1FB] p-6 rounded-xl shadow-md">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          Add Driver
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          <input
            placeholder="Name"
            value={newDriver.name}
            onChange={(e) =>
              setNewDriver({ ...newDriver, name: e.target.value })
            }
            className="input"
          />

          <input
            placeholder="Email"
            value={newDriver.email}
            onChange={(e) =>
              setNewDriver({ ...newDriver, email: e.target.value })
            }
            className="input"
          />

          <input
            placeholder="Phone"
            value={newDriver.phone}
            onChange={(e) =>
              setNewDriver({ ...newDriver, phone: e.target.value })
            }
            className="input"
          />

          <input
            placeholder="License No"
            value={newDriver.license_no}
            onChange={(e) =>
              setNewDriver({ ...newDriver, license_no: e.target.value })
            }
            className="input"
          />

          <input
            type="number"
            placeholder="Experience (years)"
            value={newDriver.experience_years}
            onChange={(e) =>
              setNewDriver({
                ...newDriver,
                experience_years: e.target.value,
              })
            }
            className="input"
          />

          <input
            type="date"
            value={newDriver.joining_date}
            onChange={(e) =>
              setNewDriver({
                ...newDriver,
                joining_date: e.target.value,
              })
            }
            className="input"
          />
        </div>

        <button
          onClick={addDriver}
          className="mt-5 w-full py-2 bg-[#0C447C] text-white rounded-lg hover:bg-[#0A3A6A] transition"
        >
          + Add Driver
        </button>
      </div>

      {/* TABLE */}
      <div className="bg-[#E6F1FB] p-6 rounded-xl shadow-md">

        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          All Drivers
        </h2>

        <input
          placeholder="Search drivers..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-3 py-2 border rounded-lg text-sm mb-4 focus:ring-2 focus:ring-[#0C447C] outline-none"
        />

        <table className="w-full text-sm text-gray-700">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">Email</th>
              <th className="px-4 py-3">License</th>
              <th className="px-4 py-3">Experience</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-center">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y">
            {filteredDrivers.map((d) => (
              <tr key={d.user_id} className="hover:bg-gray-50 transition">

                <td className="px-4 py-3 font-semibold text-gray-800">
                  {d.name}
                </td>

                <td className="px-4 py-3 text-gray-600">
                  {d.email}
                </td>

                <td className="px-4 py-3">{d.license_no}</td>
                <td className="px-4 py-3">{d.experience_years} yrs</td>

                {/* STATUS BADGE */}
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      d.status === "active"
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {d.status}
                  </span>
                </td>

                {/* ACTIONS */}
                <td className="px-4 py-3 flex justify-center gap-2">

                  <button
                    onClick={() => setSelectedDriver(d)}
                    className="px-3 py-1 text-xs bg-yellow-400 text-white rounded hover:bg-yellow-500 transition"
                  >
                    Edit
                  </button>

                  <button
                    onClick={() => toggleStatus(d)}
                    className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                  >
                    Toggle
                  </button>
                </td>
              </tr>
            ))}

            {filteredDrivers.length === 0 && (
              <tr>
                <td colSpan="6" className="text-center py-6 text-gray-400">
                  No drivers found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* EDIT */}
      {selectedDriver && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">

          {/* BACKDROP */}
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setSelectedDriver(null)}
          ></div>

          {/* MODAL */}
          <div className="relative bg-white w-full max-w-lg rounded-xl shadow-lg p-6">

            <h2 className="text-lg font-semibold mb-4">
              Edit Driver
            </h2>

            <div className="grid grid-cols-2 gap-4">

              <input
                value={selectedDriver.name}
                onChange={(e) =>
                  setSelectedDriver({
                    ...selectedDriver,
                    name: e.target.value,
                  })
                }
                className="input"
              />

              <input
                value={selectedDriver.email || ""}
                onChange={(e) =>
                  setSelectedDriver({
                    ...selectedDriver,
                    email: e.target.value,
                  })
                }
                className="input"
              />

              <input
                value={selectedDriver.license_no}
                onChange={(e) =>
                  setSelectedDriver({
                    ...selectedDriver,
                    license_no: e.target.value,
                  })
                }
                className="input"
              />

              <input
                type="number"
                value={selectedDriver.experience_years}
                onChange={(e) =>
                  setSelectedDriver({
                    ...selectedDriver,
                    experience_years: e.target.value,
                  })
                }
                className="input"
              />
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setSelectedDriver(null)}
                className="px-4 py-2 border rounded-lg"
              >
                Cancel
              </button>

              <button
                onClick={() => {
                  updateDriver();
                  setSelectedDriver(null);
                }}
                className="px-5 py-2 bg-green-600 text-white rounded-lg"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </AdminLayout>
  );
}

export default DriverDataFeed;