import React from "react";
import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();

  return (
  <div className="flex flex-col items-center mt-20">
    <h1 className="text-3xl font-bold mb-6">
      Welcome to SmartBus Scheduler
    </h1>
    <div className="flex flex-row gap-4">
      <button
        onClick={() => navigate("/login")}
        className="bg-purple-500 text-white px-6 py-3 rounded"
      >
        Login
      </button>
      <button
        onClick={() => navigate("/signup")}
        className="bg-purple-500 text-white px-6 py-3 rounded"
      >
        Sign Up
      </button>
    </div>
  </div>
);
}

export default Home;
