import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api/api";
import { jwtDecode } from "jwt-decode";
import {Link} from "react-router-dom";

function Signup() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    role: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSignup = async () => {
    try {
      const res = await API.post("/auth/signup", formData);
      const { access_token } = res.data;

      // Save token to session
      sessionStorage.setItem("token", access_token);

      // Decode token to extract role
      const decoded = jwtDecode(access_token);
      const role = decoded.role;

      setSuccess("Signup successful!");
      setError("");

      // Redirect by role
      //!!! IMPORTANT: After signing up, page directly going to authorised person because of which navbar is not shown properly. Either pass name in the navbar or ask user to log in after signing up.
      // if (role === "driver") navigate("/driver");
      // else if (role === "customer") navigate("/customer");
      navigate("/");

    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || "Signup failed. Please try again."
      );
      setSuccess("");
    }
  };

  return (
    <div className="flex flex-col items-center mt-20">
      <h2 className="text-2xl font-bold mb-4">Sign Up</h2>
      <input
        type="text"
        name="name"
        placeholder="Full Name"
        value={formData.name}
        onChange={handleChange}
        className="border p-2 m-2 w-64"
      />
      <input
        type="email"
        name="email"
        placeholder="Email"
        value={formData.email}
        onChange={handleChange}
        className="border p-2 m-2 w-64"
      />
      <input
        type="password"
        name="password"
        placeholder="Password"
        value={formData.password}
        onChange={handleChange}
        className="border p-2 m-2 w-64"
      />
      <select
        name="role"
        value={formData.role}
        onChange={handleChange}
        className="border p-2 m-2 w-64"
      >
        <option value="">Select Role</option>
        <option value="driver">Driver</option>
        <option value="customer">Customer</option>
      </select>

      <button
        onClick={handleSignup}
        className="bg-purple-500 text-white px-4 py-2 rounded"
      >
        Sign Up
      </button>
      <p>Already have an account? <Link to="/login" className="text-blue-500">Log In</Link></p>
      {error && <div className="text-red-500 mt-2">{error}</div>}
      {success && <div className="text-green-600 mt-2">{success}</div>}
    </div>
  );
}

export default Signup;
