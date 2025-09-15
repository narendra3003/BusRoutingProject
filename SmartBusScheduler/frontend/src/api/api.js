import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000",
  withCredentials: true, // send cookies
});

// Attach token automatically
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("access_token"); // sessionStorage recommended here
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

export default API;
