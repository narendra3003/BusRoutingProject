//Navbar.js

import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [name, setName] = useState(sessionStorage.getItem("name"));
  const [role, setRole] = useState(sessionStorage.getItem("role"));

  // Update navbar whenever route changes (handles login, logout, redirects)
  useEffect(() => {
    setName(sessionStorage.getItem("name"));
    setRole(sessionStorage.getItem("role"));
  }, [location.pathname]);

  const logout = () => {
    sessionStorage.clear();
    setName(null);
    setRole(null);
    navigate("/"); // or "/login" if that’s your login page
  };

  return (
    <nav className="bg-blue-600 text-white p-4 flex justify-between items-center">
      <div
        onClick={() => navigate("/")}
        className="font-bold text-lg cursor-pointer hover:text-gray-200"
      >
        SmartBus Scheduler
      </div>
      {role && (
        <div className="space-x-4 flex items-center">
          <span className="font-medium">Welcome, {name}</span>
          <button
            onClick={logout}
            className="bg-red-500 hover:bg-red-600 px-3 py-1 rounded transition"
          >
            Logout
          </button>
        </div>
      )}
    </nav>
  );
}

export default Navbar;