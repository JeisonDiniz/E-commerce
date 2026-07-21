import axios from "axios";
import { useAuthStore } from "../store/authStore";

// Em dev, o Vite faz proxy de /api -> http://localhost:8000 (ver vite.config.ts),
// então o front-end nunca precisa saber a porta real do back-end.
export const api = axios.create({
  baseURL: "/api/v1",
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);