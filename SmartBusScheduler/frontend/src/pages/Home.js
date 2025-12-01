import React from "react";
import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();

  return (
      <div className="fixed inset-0 flex flex-col justify-center items-center bg-gradient-to-br from-purple-600 via-indigo-500 to-blue-500 text-white">      <div className="text-center">
        <h1 className="text-4xl font-extrabold mb-4 drop-shadow-md">
          Welcome to <span className="text-yellow-300">SmartBus Scheduler</span>
        </h1>
        <p className="text-lg mb-10 text-gray-100">
          Plan your rides smartly and save time every day!
        </p>

        <div className="flex flex-row gap-6 justify-center">
          <button
            onClick={() => navigate("/login")}
            className="bg-white text-purple-700 font-semibold px-8 py-3 rounded-2xl shadow-lg hover:bg-purple-100 transition-all duration-200"
          >
            Login
          </button>
          <button
            onClick={() => navigate("/signup")}
            className="bg-yellow-400 text-purple-900 font-semibold px-8 py-3 rounded-2xl shadow-lg hover:bg-yellow-300 transition-all duration-200"
          >
            Sign Up
          </button>
        </div>
      </div>
    </div>
  );
}

export default Home;