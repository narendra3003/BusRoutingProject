import React, { useEffect, useState } from "react";

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
        password: "password123", // default password
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
    <div className="p-6 space-y-8">

      <h1 className="text-2xl font-bold">Drivers Management</h1>

      {/* ADD DRIVER */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">Add Driver</h2>

        <div className="grid grid-cols-2 gap-4">

          <input
            placeholder="Name"
            value={newDriver.name}
            onChange={(e) =>
              setNewDriver({ ...newDriver, name: e.target.value })
            }
            className="border p-2"
          />

          <input
            placeholder="Email"
            value={newDriver.email}
            onChange={(e) =>
              setNewDriver({ ...newDriver, email: e.target.value })
            }
            className="border p-2"
          />

          <input
            placeholder="Phone"
            value={newDriver.phone}
            onChange={(e) =>
              setNewDriver({ ...newDriver, phone: e.target.value })
            }
            className="border p-2"
          />

          <input
            placeholder="License No"
            value={newDriver.license_no}
            onChange={(e) =>
              setNewDriver({ ...newDriver, license_no: e.target.value })
            }
            className="border p-2"
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
            className="border p-2"
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
            className="border p-2"
          />
        </div>

        <button
          onClick={addDriver}
          className="mt-4 bg-purple-600 text-white px-4 py-2"
        >
          Add Driver
        </button>
      </div>

      {/* TABLE */}
      <div className="bg-white p-6 shadow rounded">
        <h2 className="font-semibold mb-4">All Drivers</h2>

        <input
          placeholder="Search drivers..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border p-2 mb-4 w-full"
        />

        <table className="w-full border text-center">
          <thead className="bg-gray-100">
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>License</th>
              <th>Experience</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {filteredDrivers.map((d) => (
              <tr key={d.user_id} className="border-t">
                <td>{d.name}</td>
                <td>{d.email}</td>
                <td>{d.license_no}</td>
                <td>{d.experience_years}</td>
                <td>{d.status}</td>

                <td className="space-x-2">
                  <button
                    onClick={() => setSelectedDriver(d)}
                    className="bg-yellow-500 text-white px-2 py-1"
                  >
                    Edit
                  </button>

                  <button
                    onClick={() => toggleStatus(d)}
                    className="bg-blue-600 text-white px-2 py-1"
                  >
                    Toggle
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* EDIT */}
      {selectedDriver && (
        <div className="bg-white p-6 shadow rounded">
          <h2 className="font-semibold mb-4">Edit Driver</h2>

          <div className="grid grid-cols-2 gap-4">
            <label className="text-left">Name:</label>
            <input
              value={selectedDriver.name}
              onChange={(e) =>
                setSelectedDriver({
                  ...selectedDriver,
                  name: e.target.value,
                })
              }
              className="border p-2"
            />

              <label className="text-left">Email:</label>
            <input
              value={selectedDriver.email || ""}
              onChange={(e) =>
                setSelectedDriver({
                  ...selectedDriver,
                  phone: e.target.value,
                })
              }
              className="border p-2"
            />

            <label className="text-left">License Number:</label>
            <input
              value={selectedDriver.license_no}
              onChange={(e) =>
                setSelectedDriver({
                  ...selectedDriver,
                  license_no: e.target.value,
                })
              }
              className="border p-2"
            />

            <label className="text-left">Experience (years):</label>
            <input
              type="number"
              value={selectedDriver.experience_years}
              onChange={(e) =>
                setSelectedDriver({
                  ...selectedDriver,
                  experience_years: e.target.value,
                })
              }
              className="border p-2"
            />
          </div>

          <button
            onClick={updateDriver}
            className="mt-4 bg-green-600 text-white px-4 py-2"
          >
            Save Changes
          </button>
        </div>
      )}

      {message && <p className="text-purple-600">{message}</p>}
    </div>
  );
}

export default DriverDataFeed;