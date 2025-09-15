import React from "react";
import { Navigate } from "react-router-dom";
import API from "../api/api";
import { useState, useEffect } from "react";

function ProtectedRoute({ children, allowedRoles }) {
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchUser() {
      try {
        const res = await API.get("/auth/me", { withCredentials: true }); 
        setRole(res.data.role);
      } catch (err) {
        setRole(null);
      } finally {
        setLoading(false);
      }
    }
    fetchUser();
  }, []);

  if (loading) return <div>Loading...</div>;

  if (!role) return <Navigate to="/" />; // not logged in
  if (!allowedRoles.includes(role)) {
    if (role === "customer") return <Navigate to="/customer" />;
    else if (role === "admin") return <Navigate to="/admin" />;
    else if (role === "driver") return <Navigate to="/driver" />;
  }

  return children;
}

export default ProtectedRoute;

