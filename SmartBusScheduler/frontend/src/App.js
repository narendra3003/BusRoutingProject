import React from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import LoginForm from "./components/LoginForm";
import CustomerDashboard from "./pages/CustomerDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import DriverDashboard from "./pages/DriverDashboard";
import Signup from "./components/SignUp";
import ProtectedRoute from "./components/ProtectedRoute";
import Unauthorized from "./pages/Unauthorized";
import StopsDataFeed from "./pages/StopsDataFeed";
import RoutesDataFeed from "./pages/RoutesDataFeed";
import BusDataFeed from "./pages/BusDataFeed";
import ConductorDashboard from "./pages/conductor";
import AdminScheduleManagement from "./pages/schedule";

function App() {
  const location = useLocation();

  // ✅ Show Navbar only on dashboard routes
  const showNavbar = ["/customer", "/admin", "/driver"].includes(location.pathname);

  return (
    <div className="min-h-screen bg-gray-100">
      {/* ✅ Conditionally render Navbar */}
      {showNavbar && <Navbar />}

      <div className="p-4">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<LoginForm />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          <Route
            path="/customer"
            element={
                <CustomerDashboard />
            }
          />
          <Route
            path="/conductor/dashboard"
            element={
                <ConductorDashboard />
            }
          />
          <Route
            path="/schedule"
            element={
                <AdminScheduleManagement />
            }
          />

          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/driver"
            element={
              <ProtectedRoute allowedRoles={["driver"]}>
                <DriverDashboard />
              </ProtectedRoute>
            }
          />
          {/* Route for stops data feed */}
          <Route path="/stops-data-feed" 
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <StopsDataFeed />
              </ProtectedRoute>
            }/>
        <Route path="/routes-data-feed" 
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <RoutesDataFeed />
              </ProtectedRoute>
            }/>
        <Route path="/buses-data-feed" 
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <BusDataFeed />
              </ProtectedRoute>
            }/>
          
        </Routes>
      </div>
    </div>
  );
}

export default App;