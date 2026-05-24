import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {jwtDecode} from "jwt-decode";
import API from "../api/api";
import { Link } from "react-router-dom";

function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await API.post("/auth/login", formData);
      const { access_token, token_type } = res.data;

      // Save token
      sessionStorage.setItem("token", access_token);
      
      //LoginForm.js

// Decode token
      const decoded = jwtDecode(access_token);
      const role = decoded.role;
      const name = decoded.name || username; // depends on your token structure

      sessionStorage.setItem("name", name);
      sessionStorage.setItem("role", role);

      
      if(role === "admin") navigate("/admin");
      else if(role === "customer") navigate("/customer");
      else if(role === "driver") navigate("/driver");
      else navigate("/"); // redirect after login

    } catch (err) {
      setError("Invalid credentials");
    }
  };

  return (
  <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0C447C] to-indigo-100">

    {/* CARD */}
    <div className="bg-white w-full max-w-md p-8 rounded-2xl shadow-lg">

      {/* HEADER */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">
          Welcome Back
        </h2>
        <p className="text-sm text-gray-500">
          Login to your account
        </p>
      </div>

      {/* FORM */}
      <div className="space-y-4">

        <input
          placeholder="Username"
          value={username}
          onChange={e => setUsername(e.target.value)}
          className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0C447C]"
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0C447C]"
        />

        <button
          onClick={handleLogin}
          className="w-full py-2 bg-[#0C447C] text-white rounded-lg hover:bg-[#0A3A6B] transition font-medium"
        >
          Login
        </button>
      </div>

      {/* ERROR */}
      {error && (
        <div className="mt-4 text-sm text-red-600 text-center">
          {error}
        </div>
      )}
    </div>
  </div>
);
}

export default LoginForm;