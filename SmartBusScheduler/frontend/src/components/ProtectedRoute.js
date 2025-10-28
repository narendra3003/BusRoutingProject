import React from "react";
import { Navigate } from "react-router-dom";
import {jwtDecode} from "jwt-decode";


const ProtectedRoute = ({ children, allowedRoles }) => {
  const token = sessionStorage.getItem("token");

  if (!token) {
    // No token → not logged in
    return <Navigate to="/login" replace />;
  }

  try {
    const decoded = jwtDecode(token);
    const userRole = decoded.role;

    // Optional: check token expiry
    if (decoded.exp * 1000 < Date.now()) {
      sessionStorage.clear();
      return <Navigate to="/login" replace />;
    }

    // If allowedRoles is passed, verify role
    if (allowedRoles && !allowedRoles.includes(userRole)) {
      return <Navigate to="/unauthorized" replace />;
    }

    // All good → show the protected content
    return children;
  } catch (err) {
    console.error("Invalid token:", err);
    sessionStorage.clear();
    return <Navigate to="/login" replace />;
  }
};

export default ProtectedRoute;