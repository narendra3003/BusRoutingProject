import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000",
});

// Add token header automatically
API.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default API;
