import React from "react";
import { Link } from "react-router-dom";

function Unauthorized() {
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-3xl font-bold text-red-600 mb-4">Access Denied</h1>
      <p className="text-gray-700 mb-4">
        You do not have permission to view this page.
      </p>
      <Link to="/login" className="text-blue-500 underline">
        Go back to Login
      </Link>
    </div>
  );
}

export default Unauthorized;