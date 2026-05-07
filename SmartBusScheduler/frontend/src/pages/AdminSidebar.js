// Sidebar.jsx
import React, { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Map,
  Database,
  Route,
  Bus,
  User,
  Clock,
  Calendar,
  AlertCircle,
  AlertTriangle,
  Menu,
  LogOut,
} from "lucide-react";

export default function Sidebar({ collapsed, setCollapsed }) {
  const location = useLocation();
  const navigate = useNavigate();
  const logout = () => {
    sessionStorage.clear();
    navigate("/"); // or "/login" if that’s your login page
  };
  const menuItems = [
    { name: "Dashboard", path: "/admin", icon: LayoutDashboard },
    { name: "Stops", path: "/stops-data-feed", icon: Map },
    { name: "Routes", path: "/routes-data-feed", icon: Database },
    { name: "Route Builder", path: "/route-builder", icon: Route },
    { name: "Buses", path: "/buses-data-feed", icon: Bus },
    { name: "Drivers", path: "/driver-data-feed", icon: User },
    { name: "Schedule", path: "/schedule", icon: Clock },
    { name: "Leave", path: "/leave-approvals", icon: Calendar },
    { name: "Dispatch", path: "/dispatch", icon: AlertCircle },
    { name: "Override", path: "/override", icon: AlertTriangle },
  ];

  return (
    <div
      className={`fixed top-0 left-0 h-screen bg-white shadow-md flex flex-col transition-all duration-300
        ${collapsed ? "w-20" : "w-64"}`}
    >
      {/* TOP */}
      <div className="flex items-center justify-between p-4">
        {!collapsed && (
          <h1 className="text-lg font-bold text-purple-600">
            SmartBus
          </h1>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded hover:bg-gray-100"
        >
          <Menu size={20} />
        </button>
      </div>

      {/* MENU */}
      <nav className="flex-1 px-2 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200
                ${
                  isActive
                    ? "bg-purple-100 text-purple-600"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
            >
              <Icon size={20} />

              {!collapsed && (
                <span className="text-sm font-medium">
                  {item.name}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="px-2 pb-4 mt-auto">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 hover:text-gray-900"
          >
            <LogOut size={20} />
            {!collapsed && (
              <span className="text-sm font-medium">
                Logout
              </span>
            )}
          </button>
        </div>
      </div>
  );
}