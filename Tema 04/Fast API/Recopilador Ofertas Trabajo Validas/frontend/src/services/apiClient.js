import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:7860',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: add Authorization header
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 and other errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const path = window.location.pathname;
      // Only redirect if not on public pages and not already on auth pages
      if (
        !path.includes('/auth/login') &&
        !path.includes('/auth/register') &&
        path !== '/' // Don't redirect from LandingPage
      ) {
        // Token expired, clear storage and redirect to login
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/auth/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
