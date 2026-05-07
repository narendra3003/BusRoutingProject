import React from "react";
import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();

  return (
  <div className="min-h-screen w-full flex flex-col bg-gradient-to-br from-purple-600 via-indigo-500 to-blue-500 text-white">

    {/* NAVBAR */}
    <div className="w-full flex justify-between items-center px-8 py-4">
      <h1 className="text-xl font-bold tracking-wide">
        SmartBus Scheduler
      </h1>

      <div className="space-x-4">
        <button
          onClick={() => navigate("/login")}
          className="px-4 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition"
        >
          Login
        </button>

      </div>
    </div>

    {/* HERO SECTION */}
    <div className="flex-1 flex flex-col justify-center items-center text-center px-6">

      <h1 className="text-5xl font-extrabold mb-6 leading-tight drop-shadow-lg">
        Smarter Bus Scheduling <br />
        <span className="text-yellow-300">Built for Efficiency</span>
      </h1>

      <p className="text-lg text-gray-100 max-w-2xl mb-10">
        Manage routes, drivers, buses, and schedules in one unified system.
        Designed for administrators to streamline operations and reduce delays.
      </p>

      <div className="flex gap-6">
        <button
          onClick={() => navigate("/login")}
          className="bg-white text-purple-700 font-semibold px-8 py-3 rounded-xl shadow-lg hover:bg-purple-100 transition"
        >
          Get Started
        </button>

        <button
          onClick={() => navigate("/signup")}
          className="bg-yellow-400 text-purple-900 font-semibold px-8 py-3 rounded-xl shadow-lg hover:bg-yellow-300 transition"
        >
          Create Account
        </button>
      </div>
    </div>

    {/* FEATURES SECTION */}
    <div className="bg-white/10 backdrop-blur-md py-10 px-6">
      <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-6 text-center">

        <div className="bg-white/10 p-6 rounded-xl">
          <h3 className="font-semibold text-lg mb-2">
            Route Management
          </h3>
          <p className="text-sm text-gray-200">
            Create and optimize routes with ease using an intuitive interface.
          </p>
        </div>

        <div className="bg-white/10 p-6 rounded-xl">
          <h3 className="font-semibold text-lg mb-2">
            Driver & Bus Control
          </h3>
          <p className="text-sm text-gray-200">
            Assign drivers and buses efficiently with real-time availability.
          </p>
        </div>

        <div className="bg-white/10 p-6 rounded-xl">
          <h3 className="font-semibold text-lg mb-2">
            Smart Scheduling
          </h3>
          <p className="text-sm text-gray-200">
            Reduce conflicts and delays with intelligent scheduling tools.
          </p>
        </div>

      </div>
    </div>

  </div>
);
}

export default Home;