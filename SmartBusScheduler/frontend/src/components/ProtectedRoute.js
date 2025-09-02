import React from "react";
import { Navigate } from "react-router-dom";

// Check session for role and allow access only to correct role
function ProtectedRoute({ children, allowedRoles }) {
  const role = sessionStorage.getItem("role");

  if (!role) return <Navigate to="/" />; // Not logged in
  if (!allowedRoles.includes(role)) {
    // Redirect to correct role page
    if(role === "customer") return <Navigate to="/customer" />;
    else if(role === "admin") return <Navigate to="/admin" />;
    else if(role === "driver") return <Navigate to="/driver" />;
  }
  
  return children;
}

export default ProtectedRoute;
