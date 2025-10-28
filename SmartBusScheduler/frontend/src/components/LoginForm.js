import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {jwtDecode} from "jwt-decode";
import API from "../api/api";

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
      
      const decoded = jwtDecode(access_token);

      const role = decoded.role;
      if(role === "admin") navigate("/admin");
      else if(role === "customer") navigate("/customer");
      else if(role === "driver") navigate("driver");
      else navigate("/"); // redirect after login

    } catch (err) {
      setError("Invalid credentials");
    }
  };

  return (
    <div className="flex flex-col items-center mt-20">
      <h2 className="text-2xl font-bold mb-4">Login</h2>
      <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} className="border p-2 m-2"/>
      <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className="border p-2 m-2"/>
      <button onClick={handleLogin} className="bg-purple-500 text-white px-4 py-2 rounded">Login</button>
      {error && <div className="text-red-500 mt-2">{error}</div>}
    </div>
  );
}

export default LoginForm;
