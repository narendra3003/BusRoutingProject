import React from "react";
import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import LoginForm from "./components/LoginForm";
import CustomerDashboard from "./pages/CustomerDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import DriverDashboard from "./pages/DriverDashboard";

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
    {/* <h1 className="text-3xl font-bold text-purple-600">Hello Tailwind!</h1> */}
      <Navbar />
      <div className="p-4">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<LoginForm />} />

          <Route path="/customer" element={
              <CustomerDashboard />
          }/>

          <Route path="/admin" element={
            
              <AdminDashboard />
          }/>

          <Route path="/driver" element={
              <DriverDashboard />
          }/>
        </Routes>
      </div>
    </div>
  );
}

export default App;
