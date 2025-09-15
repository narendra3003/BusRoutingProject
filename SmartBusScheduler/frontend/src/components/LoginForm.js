import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api/api";

function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      await API.post("/auth/login", { email, password }); // cookies set automatically
      const res = await API.get("/auth/me"); // returns user info
      const { user_id, name, role } = res.data;
      
      // Save session
      sessionStorage.setItem("token", token);
      sessionStorage.setItem("role", role);
      sessionStorage.setItem("name", name);

      // Redirect based on role
      if(role === "customer") navigate("/customer");
      else if(role === "admin") navigate("/admin");
      else if(role === "driver") navigate("/driver");
      else setError("Invalid role assigned.");
      
    } catch(err) {
      setError("Invalid credentials "+err);
    }
  }

  return (
    <div className="flex flex-col items-center mt-20">
      <h2 className="text-2xl font-bold mb-4">Login</h2>
      <input placeholder="Username" value={email} onChange={e => setEmail(e.target.value)} className="border p-2 m-2"/>
      <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className="border p-2 m-2"/>
      <button onClick={handleLogin} className="bg-purple-500 text-white px-4 py-2 rounded">Login</button>
      {error && <div className="text-red-500 mt-2">{error}</div>}
    </div>
  );
}

export default LoginForm;
