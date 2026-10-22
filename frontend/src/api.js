// frontend/src/api.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Interceptor: Automatically attach the JWT token from localStorage to every outgoing request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Authentication Service Functions
export const loginUser = async (username, password) => {
  const formData = new FormData();
  formData.append("username", username);
  formData.append("password", password);

  const response = await api.post("/api/login", formData);
  return response.data;
};

export const registerUser = async (userData) => {
  const response = await api.post("/api/register", userData);
  return response.data;
};

export const fetchUserProfile = async () => {
  const response = await api.get("/api/profile");
  return response.data;
};

// GitHub & AI Recommendations API Functions
// Updated to support dynamic search queries (e.g., language or topic)
export const fetchRecommendations = async (query = '', page = 1) => {
  const params = new URLSearchParams();
  if (query) params.append('query', query);
  params.append('page', page);

  const response = await api.get(`/api/recommendations?${params.toString()}`);
  return response.data;
};

export const fetchBookmarks = async () => {
  const response = await api.get('/api/bookmarks');
  return response.data;
};

export const bookmarkRepo = async (githubId) => {
  const response = await api.post(`/api/bookmarks/${githubId}`);
  return response.data;
};

export const fetchAIInsights = async (githubId) => {
  const response = await api.post(`/api/repositories/${githubId}/ai-insights`);
  return response.data;
};

export default api;
