import React from "react";
import { Link, useNavigate } from "react-router-dom";

function Navbar() {
  const navigate = useNavigate();
  const name = sessionStorage.getItem("name");
  const role = sessionStorage.getItem("role");

  const logout = () => {
    sessionStorage.clear();
    navigate("/");
  }

  return (
    <nav className="bg-purple-700 text-white p-4 flex justify-between">
      <div className="font-bold">SmartBus Scheduler</div>
      {role && (
        <div className="space-x-4">
          <span>Hi, {name} ({role})</span>
          <button onClick={logout} className="bg-red-500 px-2 py-1 rounded">Logout</button>
        </div>
      )}
    </nav>
  );
}

export default Navbar;
